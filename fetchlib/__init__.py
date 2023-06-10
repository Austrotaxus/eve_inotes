import operator
import os
import pickle
from typing import Dict, List, Tuple
from math import floor, ceil

import sqlite3
import pandas as pd
import numpy as np


from .setup import Setup, sde
from .utils import PATH


try:
    with open(PATH / "main_setup.pkl", "rb") as f:
        setup = pickle.load(f)
except Exception as e:
    print(e)
    setup = Setup()


CACHED_TABLES = sde.tables


def withdrawed_products() -> pd.DataFrame:
    res = CACHED_TABLES["products"]
    types = sde.cached_table("types")
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
        sde.cached_table("types"), left_on="productName", right_on="typeName"
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
    types = sde.cached_table("types", indx="typeID")
    return step.set_index("materialTypeID").join(
        types, how="inner", rsuffix="_prices"
    )


def full_expand(
    atomic: pd.DataFrame, step: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Method to calculate next step,atomic based on previous step,atomic
    """

    base_col_df = setup.collection.to_dataframe(
        setup.material_efficiency_impact(),
        setup.time_efficiency_impact(),
    )
    collection = enrich_collection(base_col_df)
    step = step.merge(collection, on="typeID", how="left").fillna(
        value={"me_impact": 1.0, "te_impact": 1.0, "run": 2**10}
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
    types = sde.cached_table("types")
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
    types = sde.cached_table("types", indx="typeName")
    init = init.set_index("typeName").join(types)
    init = init[["typeID", "quantity"]]
    if len(init.index) != len(amounts):
        raise ValueError("No such product in database!")
    return init


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
    d = Decomposition(step=table)
    try:
        sequence = [d.required_materials] + d.prety_steps
    except (AssertionError, ValueError) as e:
        result.append(e)
        return result
    for i, table in enumerate(sequence):
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


class Decomposition:
    def __init__(self, *, atomic=None, step):
        if atomic is None:
            atomic = self.empty_atomic()

        # Some dark magic from pandas and sde
        self.atomic, self.step = full_expand(atomic=atomic, step=step)

        if not self.is_final:
            self.child = Decomposition(atomic=self.atomic, step=self.step)
        else:
            self.child = None

    def from_tuple(self, tuples: List[Tuple[str, int]]):
        """
        Method to create initial Pandas dataframe
        """
        init = pd.DataFrame(
            amounts, columns=["typeName", "quantity"]
        ).set_index("typeName")
        types = sde.cached_table("types", indx="typeName")
        init = init.join(types)
        init = init[["typeID", "quantity"]]
        if len(init.index) != len(amounts):
            raise ValueError("No such product in database!")

        return Decomposition(step=init)

    @property
    def is_final(self):
        return self.step.shape[0] == 0

    def _required_materials(self):
        if self.is_final:
            return self.atomic
        else:
            return self.atomic.append(self.child._required_materials())

    def __next__(self):
        return self.child

    def __iter__(self):
        return self

    @property
    def required_materials(self):
        return materials_from_atomic(self._required_materials())

    @property
    def prety_step(self):
        step = self.step.copy()
        step = append_products(step)[["typeID", "quantity", "activityID"]]
        # BPC id instead of material ID
        step = step.reset_index()
        step["typeID"] = step["index"]
        step = step.drop(columns=["index"])
        types = sde.cached_table("types", indx="typeID")
        step = append_products(step).join(types)
        step["runs_required"] = step["quantity"] / step["quantity_product"]
        return step[["typeName", "quantity", "runs_required", "activityID"]]

    @property
    def prety_steps(self) -> List[pd.DataFrame]:
        if not self.is_final:
            return self.child.prety_steps + [self.prety_step]
        return []

    @classmethod
    def empty_atomic(cls):
        dataframe = pd.DataFrame(
            [], columns=["typeID", "quantity", "basePrice"]
        ).set_index("typeID")
        return dataframe

    def __repr__(self):
        return f"Decomposition(steps: {self.step}, atomics: {self.atomic})"

    def __str__(self):
        result = ["Required materials:"]
        result.append(self.required_materials.to_csv(index=False, sep="\t"))
        for i, table in enumerate(self.prety_steps, start=1):
            result.append("Step {} is: ".format(i))
            result.append(table.to_csv(index=False, sep="\t"))
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
                    result.append(f"{k} : [{v}]")
            if reac:
                for k, v in balance_runs(reac, setup.reaction_lines).items():
                    result.append(f"{k} : [{v}]")

        return "\n".join(result)
