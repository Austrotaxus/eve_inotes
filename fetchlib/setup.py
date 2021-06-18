from typing import Iterable

import pickle
from pathlib import Path

from fetchlib.importer import Importer
from fetchlib.utils import (
    BlueprintCollection,
    BP,
    ProductionClasses,
    SpaceTypes,
    CitadelTypes,
    Rigs,
    PATH,
)

importer = Importer()


class Setup:
    def __init__(
        self,
    ):
        self.citadel_type = CitadelTypes.RAITARU
        self.space_type = SpaceTypes.NULL_WH
        self.rig_set = []
        self.skills = None
        self.collection = BlueprintCollection(self.initial_collection())
        self.reaction_lines = 20
        self.production_lines = 20
        self._non_productables = {
            "Nitrogen Fuel Block Blueprint",
            "Hydrogen Fuel Block Blueprint",
            "Helium Fuel Block Blueprint",
            "Oxygen Fuel Block Blueprint",
            "R.A.M.- Starship Tech Blueprint",
            "Scorpion Blueprint",
        }

    @classmethod
    def default_impact(cls):
        members = ProductionClasses.to_dict().values()
        res = {m: 1.0 for m in members}
        return res

    def initial_collection(self):
        d = importer.component_by_classes
        for tp, lst in d.items():
            for name in lst:
                yield BP(name, 0.1, 0.2, p_type=tp)

    def non_productables(self):
        return self._non_productables

    def me_impact(self):
        citadel_impact = 1 - (
            (self.citadel_type in (CitadelTypes.RAITARU,)) * 0.01
        )

        impact_dict = Setup.default_impact()

        for rig in self.rig_set:
            rig_dict = rig.represent_me(self.space_type)
            for affected, rig_me in rig_dict.items():
                impact_dict[affected] = 1.0 - rig_me

        for key in impact_dict.keys():
            impact_dict[key] *= citadel_impact
        return impact_dict

    def te_impact(self):
        return {}

    def add_to_collection(self, prints: Iterable[BP]):
        names = [p.name for p in prints]
        diff = set(names) - set(importer.tables["types"]["typeName"])
        if diff:
            raise ValueError("Unknow typenames:{}".format(diff))
        self.collection.add(prints)

    def save_setup(self):
        with open(PATH / "main_setup.pkl", "wb") as f:
            pickle.dump(self, f)

    def set_lines_amount(self, reaction: int, production: int):
        self.reaction_lines = reaction
        self.production_lines = production
