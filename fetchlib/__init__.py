import sqlite3
import os
import pandas as pd
import numpy as np

from .utils import my_collection, NON_PRODUCTABLE
from .importer import Importer

db_importer = Importer()

CACHED_TABLES = db_importer.tables


def indexed_types():
    return CACHED_TABLES["types"].set_index("typeID")


def norm_types():
    return CACHED_TABLES["types"]


def withdrawed_products():
    res = CACHED_TABLES["products"]
    types = norm_types()
    res = res[res["activityID"].isin((1, 11))]
    removes = types[types["typeName"].isin(NON_PRODUCTABLE)]["typeID"]
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
        # 4 production
        if x.activityID == 1:
            run_price = int(np.ceil(x.quantity_materials * run_size * x.me))
            r_req = jobs_required * run_size
            run_price = np.maximum(run_price, run_size)

            trim_size = x.quantity - run_size * jobs_required
            trim_price = int(np.ceil(x.quantity_materials * trim_size * x.me))
            trim_price = np.maximum(trim_price, trim_size)

            # FIXME Need some testings
            run_price = (run_price * jobs_required) + trim_size

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
    collection = enrich_collection(my_collection.to_dataframe())
    types = norm_types()
    assert product in types["typeName"].values, "No such product in database!"
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
            value={"me": 1, "te": 1, "run": 2 ** 10}
        )
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

        atomic = atomic.append(
            step[~step["typeID"].isin(withdrawed_products()["productTypeID"])]
        )

        step = step[
            step["typeID"].isin(withdrawed_products()["productTypeID"])
        ]
        steps.append(step)

        if step.shape[0] == 0:
            break

    a = (
        atomic[["typeID", "quantity"]]
        .astype({"typeID": "int32"})
        .groupby("typeID")
        .sum()
    )

    a = a.join(types.set_index("typeID"), lsuffix="-atom_")[
        ["quantity", "typeName"]
    ]

    return reversed(steps), a


def create_production_schema(product, run_size):
    steps, ms = ultimate_decompose(product, run_size)
    for s in steps:
        if s.empty:
            yield ms
            continue
        v = append_products(s).join(norm_types().set_index("typeID"))
        v["runs_required"] = v["quantity"] / v["quantity_product"]
        yield v[
            [
                "typeID",
                "typeName",
                "quantity",
                "runs_required",
            ]
        ]
