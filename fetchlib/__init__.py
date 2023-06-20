import operator
from typing import Dict

import numpy as np


def balancify_runs(decomposition: "Decomposition", setup) -> str:
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
