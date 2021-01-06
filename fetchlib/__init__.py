import operator
import os
import pickle
from typing import Dict
from math import floor, ceil

import sqlite3
import pandas as pd
import numpy as np


from .setup import Setup, importer

try:
    with open("fetchlib/setups/main_setup.pkl", "rb") as f:
        setup = pickle.load(f)
except Exception as e:
    print(e)
    setup = Setup()


CACHED_TABLES = importer.tables


def indexed_types():
    return CACHED_TABLES["types"].set_index("typeID")


def norm_types():
    return CACHED_TABLES["types"]


def withdrawed_products():
    res = CACHED_TABLES["products"]
    types = norm_types()
    res = res[res["activityID"].isin((1, 11))]
    removes = types[types["typeName"].isin(setup.non_productables())]["typeID"]
    res = res[~res["typeID"].isin(removes)]
    return res


def alterated_materials():
    # Remove everything but 'reaction' and 'production'
    materials = CACHED_TABLES["materials"]
    res = materials[materials["activityID"].isin([1, 11])]
    return res.set_index("typeID")


def enrich_collection(col_df):
    collection_df = col_df.merge(
        norm_types(), left_on="productName", right_on="typeName"
    )[["typeName", "typeID", "run", "me", "te"]]
    return collection_df


def count_required(step):
    def price_in_materials(x):
        run_size = np.minimum(x.quantity, x.run)
        jobs_required = (np.floor(x.quantity / run_size)).astype("int32")
        # For production
        if x.activityID == 1:
            run_price = int(np.ceil(x.quantity_materials * run_size * x.me))
            r_req = jobs_required * run_size
            run_price = np.maximum(run_price, run_size)

            trim_size = x.quantity - run_size * jobs_required
            trim_price = int(np.ceil(x.quantity_materials * trim_size * x.me))
            trim_price = np.maximum(trim_price, trim_size)

            run_price = (run_price * jobs_required) + trim_price

        # For reaction
        elif x.activityID == 11:
            r_req = int(np.ceil((x.quantity / x.quantity_product)))
            run_price = x.quantity_materials * r_req
        else:
            raise Exception("Unknown reaction ID")
        return run_price

    def runs_required(x):
        run_size = np.minimum(x.quantity, x.run)
        jobs_required = (np.ceil(x.quantity / run_size)).astype("int32")
        # count for production
        if x.activityID == 1:
            r_req = jobs_required * run_size
        # count for reaction
        elif x.activityID == 11:
            r_req = int(np.ceil((x.quantity / x.quantity_product)))
        else:
            r_req = 0
        return r_req

    run_price = step.apply(price_in_materials, axis=1)
    runs_required = step.apply(runs_required, axis=1)
    return run_price, runs_required


def append_products(step):
    return step.set_index("typeID").join(
        withdrawed_products().set_index("productTypeID"),
        rsuffix="_product",
        how="inner",
    )


def append_materials(step):
    return step.set_index("typeID").join(
        alterated_materials(), how="inner", rsuffix="_materials"
    )


def append_prices(step):
    return step.set_index("materialTypeID").join(
        indexed_types(), how="inner", rsuffix="_prices"
    )


def ultimate_decompose(product, run_size):
    base_col_df = setup.collection.to_df(
        setup.me_impact(),
        setup.te_impact(),
    )
    collection = enrich_collection(base_col_df)
    types = norm_types()

    if product not in types["typeName"].values:
        raise ValueError("No such product in database!")

    # Init table is about root of our production
    init_table = types[types["typeName"] == product]
    init_table = init_table[["typeID"]]
    init_table["quantity"] = run_size

    atomic = pd.DataFrame(
        [], columns=["typeID", "quantity", "basePrice"]
    ).set_index("typeID")

    step = init_table
    steps = [step]

    while True:
        step = step.merge(collection, on="typeID", how="left").fillna(
            value={"me": 0, "te": 0, "run": 2 ** 10}
        )
        # Add info to table to understand what we would need pn the next steps

        with_products = append_products(step)
        with_materials = append_materials(with_products)
        with_prices = append_prices(with_materials)

        step = with_prices
        step["quantity"], step["runs_required"] = count_required(step)
        step = step.groupby(step.index).sum()

        step = (
            step[["quantity"]]
            .reset_index()
            .rename({"index": "typeID"}, axis="columns")
        )

        # Atomic is everything that couln't be produced and should be taken from environment
        atomic = atomic.append(
            step[~step["typeID"].isin(withdrawed_products()["productTypeID"])]
        )

        step = step[
            step["typeID"].isin(withdrawed_products()["productTypeID"])
        ]
        steps.append(step)

        if step.shape[0] == 0:
            break

    materials = (
        atomic[["typeID", "quantity"]]
        .astype({"typeID": "int32"})
        .groupby("typeID")
        .sum()
    )
    materials = materials.join(types.set_index("typeID"), lsuffix="-atom_")[
        ["typeName", "quantity"]
    ].astype({"quantity": "int32"})

    return reversed(steps), materials


def create_production_schema(product, run_size):
    steps, materials = ultimate_decompose(product, run_size)
    for step in steps:
        if step.empty:
            yield materials
            continue
        v = append_products(step).join(norm_types().set_index("typeID"))
        v["runs_required"] = v["quantity"] / v["quantity_product"]
        yield v[
            [
                "typeName",
                "quantity",
                "runs_required",
            ]
        ]


def balance_runs(runs_required: Dict[str, float], lines: int):
    lines_distribution = dict.fromkeys(runs_required.keys(), 1)
    load = {}
    for i in range(len(runs_required), lines):
        for k in runs_required.keys():
            load[k] = runs_required[k] / lines_distribution[k]
        max_loaded = max(load.items(), key=operator.itemgetter(1))[0]
        lines_distribution[max_loaded] += 1
    lines_load = {}
    for key, value in lines_distribution.items():
        lines_load[key] = [0] * value
        # Populate lines_load with basic values
        for i in range(len(lines_load[key])):
            lines_load[key][i] = floor(
                float(runs_required[key]) / lines_distribution[key]
            )
        # Add insufficient runs to each line
        for i in range(int(ceil(runs_required[key] - sum(lines_load[key])))):
            lines_load[key][i] += 1
    return lines_load


def output(x):
    print()
    print(x)
    print()


def output_production_chema(product, run_size: int):
    for i, table in enumerate(create_production_schema(product, run_size)):
        output("Step {} is: ".format(i))
        output(table.to_csv(index=False, sep="\t"))
        if i > 0:
            output("Balancing runs:")
            d = table.set_index("typeName").to_dict()["runs_required"]
            for k, v in balance_runs(d, 20).items():
                output((k, v))
