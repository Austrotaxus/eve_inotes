from dataclasses import dataclass, field
from typing import Iterable, Set

import pandas as pd


@dataclass(frozen=True)
class Blueprint:
    name: str
    material_efficiency: float
    time_efficiency: float
    runs: int = field(default=2**20)


class BlueprintCollection:
    """Represents collection of blueprints.

    All names of blueprint in collection are unique.
    """

    def __init__(self, prints: Iterable[Blueprint]):
        self._prints = {}
        for blueprint in prints:
            self._prints[blueprint.name] = blueprint

    def __repr__(self):
        return f"BlueprintCollection( {self.prints} )"

    def add(self, *prints):
        """Add blueprint list to the _prints.

        Args:
            prints - list of blueprints
        """
        for blueprint in prints:
            self._prints[blueprint.name] = blueprint

    def __len__(self):
        return len(self._prints)

    def get(self, key, default=None):
        return self._prints.get(key, default)

    def __getitem__(self, name):
        return self._prints[name]

    def __iter__(self):
        return iter(self._prints.values())

    @property
    def to_dataframe(self):
        """
        Returns:

            A dataframe contains information about blueprint collection indexed by 'typeName'
            For example:
                    te_impact me_impact  run
            Raven         0.8       0.9   10

            te_impact is in [0.8, 1.0]
            me_impact is in [0.9, 1.0]
        """
        names = (blueprint.name for blueprint in self)
        material_efficiencies = (
            (1 - blueprint.material_efficiency) for blueprint in self
        )
        time_efficiencies = ((1 - blueprint.time_efficiency) for blueprint in self)
        runs = (blueprint.runs for blueprint in self)
        return pd.DataFrame(
            data={
                "me_impact": material_efficiencies,
                "te_impact": time_efficiencies,
                "run": runs,
            },
            index=names,
        )
