import operator
import pickle
from typing import Dict, List, Tuple

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


class Decompositor:
    def __init__(self, sde, setup):
        self.sde = sde
        self.setup = setup

    def __call__(self, step: pd.DataFrame):
        types = self.sde.types

        cleared = step[["typeID", "quantity"]]
        base_collection = setup.collection.to_dataframe(
            self.setup.material_efficiency_impact(),
            self.setup.time_efficiency_impact(),
        )
        collection = sde.enrich_collection(base_collection)
        merged = cleared.merge(collection, on="typeID", how="left").fillna(
            value={"me_impact": 1.0, "te_impact": 1.0, "run": 2**10}
        )
        # Add info to table to understand what we would need pn the next steps
        appended = self.sde.append_everything(merged)

        to_remove = types[types["typeName"].isin(setup.non_productables())][
            "typeID"
        ]
        filtered = appended[~appended.isin(to_remove)]

        table = filtered
        table["quantity"], table["runs_required"] = self.count_required(table)

        summed = table.groupby(table.index).sum()
        quantity_table = (
            summed[["quantity"]]
            .reset_index()
            .rename({"index": "typeID"}, axis="columns")
        )
        atomic = quantity_table[
            ~quantity_table["typeID"].isin(sde.productables["productTypeID"])
            | quantity_table["typeID"].isin(to_remove)
        ]
        new_step = quantity_table[
            quantity_table["typeID"].isin(sde.productables["productTypeID"])
            & ~quantity_table["typeID"].isin(to_remove)
        ]

        return sde.atomic_materials(atomic), sde.pretify_step(new_step)

    @staticmethod
    def count_required(
        step: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
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
                        x.quantity_materials
                        * single_line_run_size
                        * x.me_impact
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
                r_req = int(
                    np.ceil(jobs_required * run_size / x.quantity_product)
                )
            # count for reaction
            elif x.activityID == 11:
                r_req = int(np.ceil((x.quantity / x.quantity_product)))
            else:
                r_req = 0
            return r_req

        run_price = step.apply(price_in_materials, axis=1)

        return run_price, runs_required


class Decomposition:
    def __init__(self, *, step, decompositor):
        self.step = step
        self.atomic, next_step = decompositor(step=step)

        if next_step.shape[0] != 0:
            self.child = Decomposition(
                step=next_step, decompositor=decompositor
            )
        else:
            self.child = None

    @property
    def is_final(self):
        return self.child is None

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
        table = self._required_materials()
        return table.groupby(["typeName"])["quantity"].sum()

    @property
    def steps(self) -> List[pd.DataFrame]:
        if not self.is_final:
            return self.child.steps + [self.step]
        return [self.step]

    @classmethod
    def empty_atomic(cls):
        dataframe = pd.DataFrame(
            [], columns=["typeID", "quantity", "typeName"]
        )
        return dataframe

    def __repr__(self):
        return f"Decomposition(steps: {self.step}, atomics: {self.atomic})"

    def __str__(self):
        result = ["Required materials:"]
        result.append(self.required_materials.to_csv(sep="\t"))
        for i, table in enumerate(self.steps, start=1):
            result.append("Step {} is: ".format(i))
            result.append(table.to_csv(index=False, sep="\t"))

        return "\n".join(result)


def balancify_runs(decomposition: Decomposition) -> str:
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

    result = []
    result = ["Balancing runs"]
    for i, table in enumerate(decomposition.steps, start=1):
        result.append(f"Balancing runs for step {i}:")
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
