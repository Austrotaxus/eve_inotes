from typing import Tuple

import numpy as np
import pandas as pd


class Decompositor:
    def __init__(self, sde, setup):
        self.sde = sde
        self.setup = setup

    def __call__(self, step: pd.DataFrame):
        types = self.sde.types

        cleared = step[["typeID", "quantity"]]
        base_collection = self.setup.collection.to_dataframe(
            self.setup.material_efficiency_impact(),
            self.setup.time_efficiency_impact(),
        )
        collection = self.sde.enrich_collection(base_collection)
        merged = cleared.merge(collection, on="typeID", how="left").fillna(
            value={"me_impact": 1.0, "te_impact": 1.0, "run": 2**10}
        )
        # Add info to table to understand what we would need pn the next steps
        appended = self.sde.append_everything(merged)

        to_remove = types[
            types["typeName"].isin(self.setup.non_productables())
        ]["typeID"]
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
            ~quantity_table["typeID"].isin(
                self.sde.productables["productTypeID"]
            )
            | quantity_table["typeID"].isin(to_remove)
        ]
        new_step = quantity_table[
            quantity_table["typeID"].isin(
                self.sde.productables["productTypeID"]
            )
            & ~quantity_table["typeID"].isin(to_remove)
        ]

        return (
            self.sde.atomic_materials(atomic),
            self.sde.pretify_step(new_step),
        )

    @classmethod
    def count_required(
        cls,
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
