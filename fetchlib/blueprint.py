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
    def __init__(self, prints: Iterable[Blueprint]):
        self._prints = {}
        for blueprint in prints:
            self._prints[blueprint.name] = blueprint

    def __repr__(self):
        return f"BlueprintCollection( {self.prints} )"

    def add(self, *prints):
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

    # FIXME should be moved to setup
    def effective_dataframe(self, material_impact={}, time_impact={}):
        """
        Calculates effective time and material efficiency
        params:
        material_impact - dict of material impacts provided by setup (rigs+citadels)
        time_impact - dict of time impacts provided by setup (rigs+citadels)
        """
        names = (blueprint.name for blueprint in self)
        material_efficiencies = (
            (1 - blueprint.material_efficiency)
            * material_impact.get(blueprint.name, 1.0)
            for blueprint in self
        )
        time_efficiencies = (
            (1 - blueprint.time_efficiency) * time_impact.get(blueprint.name, 1.0)
            for blueprint in self
        )
        runs = (blueprint.runs for blueprint in self)
        return pd.DataFrame(
            data={
                "productName": names,
                "me_impact": material_efficiencies,
                "te_impact": time_efficiencies,
                "run": runs,
            }
        )
