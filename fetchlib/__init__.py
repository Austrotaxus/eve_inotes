import operator
import os
import pickle
from typing import Dict, List, Tuple
from math import floor, ceil

import sqlite3
import pandas as pd
import numpy as np


from .setup import Setup, importer
from .utils import PATH


try:
    with open(PATH / "main_setup.pkl", "rb") as f:
        setup = pickle.load(f)
except Exception as e:
    print(e)
    setup = Setup()


CACHED_TABLES = importer.tables


def indexed_types() -> pd.DataFrame:
    return CACHED_TABLES["types"].set_index("typeID")


def norm_types() -> pd.DataFrame:
    return CACHED_TABLES["types"]


def withdrawed_products() -> pd.DataFrame:
    res = CACHED_TABLES["products"]
    types = norm_types()
    res = res[res["activityID"].isin((1, 11))]
    removes = types[types["typeName"].isin(setup.non_productables())]["typeID"]
    res = res[~res["typeID"].isin(removes)]
    return res


def alterated_materials() -> pd.DataFrame:
    # Remove everything but 'reaction' and 'production'
    materials = CACHED_TABLES["materials"]
    res = materials[materials["activityID"].isin([1, 11])]
    return res.set_index("typeID")


def enrich_collection(col_df: pd.DataFrame) -> pd.DataFrame:
    collection_df = col_df.merge(
        norm_types(), left_on="productName", right_on="typeName"
    )[["typeName", "typeID", "run", "me_impact", "te_impact"]]
    return collection_df


def count_required(step: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    def price_in_materials(x):
        ideal_run_size = np.ceil(x.quantity / x.quantity_product)
        single_line_run_size = int(np.minimum(ideal_run_size, x.run))
        paralel_jobs_required = np.ceil(
            (x.quantity / (single_line_run_size * x.quantity_product))
        ).astype("int32")
        # For production
        if x.activityID == 1:
            single_line_run_price = int(
                np.ceil(
                    x.quantity_materials * single_line_run_size * x.me_impact
                )
            )
            single_line_run_price = np.maximum(
                single_line_run_price, single_line_run_size
            )

            trim_size = (
                x.quantity
                - single_line_run_size
                * paralel_jobs_required
                * x.quantity_product
            )
            trim_price = int(
                np.ceil(
                    x.quantity_materials
                    * trim_size
                    * x.me_impact
                    / x.quantity_product
                )
            )
            trim_price = np.maximum(trim_price, trim_size)

            run_price = (
                single_line_run_price * paralel_jobs_required
            ) + trim_price

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
            r_req = int(np.ceil(jobs_required * run_size / x.quantity_product))
        # count for reaction
        elif x.activityID == 11:
            r_req = int(np.ceil((x.quantity / x.quantity_product)))
        else:
            r_req = 0
        return r_req

    run_price = step.apply(price_in_materials, axis=1)
    runs_required = step.apply(runs_required, axis=1)
    return run_price, runs_required


def append_products(step: pd.DataFrame) -> pd.DataFrame:
    return step.set_index("typeID").join(
        withdrawed_products().set_index("productTypeID"),
        rsuffix="_product",
        how="inner",
    )


def append_materials(step: pd.DataFrame) -> pd.DataFrame:
    return step.set_index("typeID").join(
        alterated_materials(), how="inner", rsuffix="_materials"
    )


def append_prices(step: pd.DataFrame) -> pd.DataFrame:
    return step.set_index("materialTypeID").join(
        indexed_types(), how="inner", rsuffix="_prices"
    )


def full_expand(
    atomic: pd.DataFrame, step: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Method to calculate next step,atomic based on previous step,atomic
    """

    base_col_df = setup.collection.to_df(
        setup.me_impact(),
        setup.te_impact(),
    )
    collection = enrich_collection(base_col_df)
    step = step.merge(collection, on="typeID", how="left").fillna(
        value={"me_impact": 1.0, "te_impact": 1.0, "run": 2 ** 10}
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
    atomic = atomic.append(
        step[~step["typeID"].isin(withdrawed_products()["productTypeID"])]
    )
    step = step[step["typeID"].isin(withdrawed_products()["productTypeID"])]

    return atomic, step


def materials_from_atomic(atomic: pd.DataFrame) -> pd.DataFrame:
    """
    Method for creating table with quantities and names from id table
    """
    types = norm_types()
    materials = (
        atomic[["typeID", "quantity"]]
        .astype({"typeID": "int64"})
        .groupby("typeID")
        .sum()
    )
    materials = materials.join(types.set_index("typeID"), lsuffix="-atom_")[
        ["typeName", "quantity"]
    ].astype({"quantity": "int64"})

    return materials


def prepare_init_table(amounts: List[Tuple[str, int]]) -> pd.DataFrame:
    """
    Method to create initial Pandas dataframe
    """
    init = pd.DataFrame(amounts, columns=["typeName", "quantity"])
    init = init.set_index("typeName").join(norm_types().set_index("typeName"))
    init = init[["typeID", "quantity"]]
    if len(init.index) != len(amounts):
        raise ValueError("No such product in database!")
    return init


def ultimate_decompose(
    table: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    def prettify_steps(steps):
        for i in range(len(steps)):
            steps[i] = append_products(steps[i])[
                ["typeID", "quantity", "activityID"]
            ]
            # BPC id instead of material ID
            steps[i] = steps[i].reset_index()
            steps[i]["typeID"] = steps[i]["index"]
            steps[i] = steps[i].drop(columns=["index"])
        return reversed(steps)

    atomic = pd.DataFrame(
        [], columns=["typeID", "quantity", "basePrice"]
    ).set_index("typeID")
    step = table
    steps = [step]
    while True:
        atomic, step = full_expand(atomic, step)
        if step.shape[0] == 0:
            break
        steps.append(step)

    materials = materials_from_atomic(atomic)
    pretty_steps = prettify_steps(steps)

    return pretty_steps, materials


def create_production_schema(table: pd.DataFrame):
    """
    Generator which yields steps one by one
    """
    steps, materials = ultimate_decompose(table)
    combined = [materials] + [*steps]
    for value in combined:
        if "activityID" not in value.columns:
            yield value
            continue
        v = append_products(value).join(norm_types().set_index("typeID"))
        v["runs_required"] = v["quantity"] / v["quantity_product"]
        yield v[["typeName", "quantity", "runs_required", "activityID"]]


def balance_runs(runs_required: Dict[str, float], lines: int):
    """Method to calculate lines loading according to lines amount"""
    # FIXME Job running time is not counted right now
    lines_distribution = dict.fromkeys(runs_required.keys(), 1)
    load = {}

    for i in range(len(runs_required), lines):
        for k in runs_required.keys():
            load[k] = runs_required[k] / lines_distribution[k]
        max_loaded = max(load.items(), key=operator.itemgetter(1))[0]
        lines_distribution[max_loaded] += 1
    lines_load = {}

    for key, value in lines_distribution.items():
        lines_load[key] = ""
        int_runs_required = int(np.ceil(runs_required[key]))
        div = int_runs_required // value
        reminder = int_runs_required % value
        line_load = "{} x {}".format(div, value - reminder)
        if reminder > 0:
            line_load = line_load + " + {} x {}, total - {}".format(
                div + 1, reminder, value
            )
        lines_load[key] = line_load
    return lines_load


def production_schema(table: pd.DataFrame) -> List[str]:
    """
    Method to represent the whole prod schema as list of steps
    """
    result = []
    try:
        sequence = [*enumerate(create_production_schema(table))]
    except (AssertionError, ValueError) as e:
        result.append(e)
        return result
    for i, table in sequence:
        result.append("Step {} is: ".format(i))
        result.append(table.to_csv(index=False, sep="\t"))
        if i > 0:
            result.append("Balancing runs:")
            prod = (
                table[table["activityID"] == 1]
                .set_index("typeName")
                .to_dict()["runs_required"]
            )
            reac = (
                table[table["activityID"] == 11]
                .set_index("typeName")
                .to_dict()["runs_required"]
            )

            if prod:
                for k, v in balance_runs(prod, setup.production_lines).items():
                    result.append("{} : [{}]".format(k, v))
            if reac:
                for k, v in balance_runs(reac, setup.reaction_lines).items():
                    result.append("{} : [{}]".format(k, v))

    return result
