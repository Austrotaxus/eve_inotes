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


def full_expand(step: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Method to calculate next step,atomic based on previous step,atomic
    """
    types = sde.types

    base_col_df = setup.collection.to_dataframe(
        setup.material_efficiency_impact(),
        setup.time_efficiency_impact(),
    )
    collection = sde.enrich_collection(base_col_df)
    step = step.merge(collection, on="typeID", how="left").fillna(
        value={"me_impact": 1.0, "te_impact": 1.0, "run": 2**10}
    )
    # Add info to table to understand what we would need pn the next steps

    appended = sde.append_everything(step)

    removes = types[types["typeName"].isin(setup.non_productables())]["typeID"]
    step = appended[~appended.isin(removes)]

    step["quantity"], step["runs_required"] = count_required(step)
    step = step.groupby(step.index).sum()
    step = (
        step[["quantity"]]
        .reset_index()
        .rename({"index": "typeID"}, axis="columns")
    )
    atomic = step[
        ~step["typeID"].isin(sde.productables["productTypeID"])
        | step["typeID"].isin(removes)
    ]
    step = step[
        step["typeID"].isin(sde.productables["productTypeID"])
        & ~step["typeID"].isin(removes)
    ]

    return atomic, step


def materials_from_atomic(atomic: pd.DataFrame) -> pd.DataFrame:
    """
    Method for creating table with quantities and names from id table
    """
    types = sde.types
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


class Decompositor:
    def __init__(self, sde=sde, setup=setup):
        self.sde = sde
        self.setup = setup

    def __apply__(self, step: pd.DataFrame):
        pass


class Decomposition:
    def __init__(self, *, step, decompose_function=full_expand):
        self.atomic, self.step = decompose_function(step=step)

        if not self.is_final:
            self.child = Decomposition(step=self.step)
        else:
            self.child = None

    @classmethod
    def from_tuple(cls, tuples: List[Tuple[str, int]]):
        """
        Method to create initial Pandas dataframe
        """
        # FIXME get rid of sde dependency
        init = pd.DataFrame(
            tuples, columns=["typeName", "quantity"]
        ).set_index("typeName")
        types = sde.types.set_index("typeName")
        init = init.join(types)
        init = init[["typeID", "quantity"]]
        if len(init.index) != len(tuples):
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

    def __iter__(self):
        def gen_helper():
            init = self
            while self.child:
                yield init.step
                init = self.child
            yield init.step

        return gen_helper()

    @property
    def required_materials(self):
        return materials_from_atomic(self._required_materials())

    @property
    def prety_step(self):
        # FIXME get rid of sde dependency
        step = self.step.copy()
        step = sde.append_products(step)[["typeID", "quantity", "activityID"]]
        # BPC id instead of material ID
        step = step.reset_index()
        step["typeID"] = step["index"]
        step = step.drop(columns=["index"])
        types = sde.types.set_index("typeID")
        step = sde.append_products(step).join(types)
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
        # FIXME get_rid of sde dependency
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
