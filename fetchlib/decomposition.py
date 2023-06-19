from typing import List

import pandas as pd


class Decomposition:
    def __init__(self, *, step, decompositor):
        self.step = step
        self.atomic, next_step = decompositor(step=step)

        if not self._finalize_condition(next_step):
            self.child = Decomposition(step=next_step, decompositor=decompositor)
        else:
            self.child = None

    @property
    def is_final(self):
        return self.child is None

    @classmethod
    def _finalize_condition(cls, next_step):
        return next_step.shape[0] == 0

    def _required_materials(self):
        if self.is_final:
            return self.atomic
        else:
            return self.atomic.append(self.child._required_materials())

    def __iter__(self):
        def gen_helper():
            init = self
            while init.child:
                yield init.step
                init = init.child
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
        dataframe = pd.DataFrame([], columns=["typeID", "quantity", "typeName"])
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
