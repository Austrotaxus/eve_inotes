from typing import List

import pandas as pd


class Decomposition:
    """Decomposition is a recursive object which contain steps(what to produce)
    atomic(elementary materials required for this step) and Decomposition object
    for non-atomic(productable) items required for this step
    """

    def __init__(self, *, step, decompositor):
        """
        Args:
            step - dataframe we want to decompose
            decompositor - strategy of decomposition
        """

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
            return pd.concat([self.atomic, self.child._required_materials()])

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
        """
        Returns:
            Dataframe of elementary materials required for production
            defined by Decomposition.
        """
        table = self._required_materials()
        return table.groupby(["typeName"])["quantity"].sum()

    @property
    def steps(self) -> List[pd.DataFrame]:
        """
        Returns:
            List of dataframes with production instructions to implement production
            defined by Decomposition.
        """
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
