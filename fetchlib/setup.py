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
)

importer = Importer()


class Setup:
    def __init__(
        self,
    ):
        self.citadel_type = CitadelTypes.RAITARU
        self.space_type = SpaceTypes.NULL_WH
        self.rig_set = [Rigs.ADV_ME_COMP_1]  # , Rigs.ADV_ME_SMALL_1]
        self.skills = None
        self.collection = BlueprintCollection(self.initial_collection())
        self._non_productables = {
            "Nitrogen Fuel Block Blueprint",
            "Hydrogen Fuel Block Blueprint",
            "Helium Fuel Block Blueprint",
            "Oxygen Fuel Block Blueprint",
            "R.A.M.- Starship Tech Blueprint",
        }

    @classmethod
    def default_efficiences(cls):
        members = ProductionClasses.to_dict().values()
        res = {m: 1.0 for m in members}
        return res

    def initial_collection(self):
        d = importer.component_by_classes
        for tp, lst in d.items():
            for name in lst:
                yield BP(name, 0.9, 0.8, p_type=tp)

    def non_productables(self):
        return self._non_productables

    def me_mods(self):
        citadel_impact = (self.citadel_type in (CitadelTypes.RAITARU,)) * 0.01

        resulting_dict = Setup.default_efficiences()

        for rig in self.rig_set:
            rig_impact = rig.represent_me(self.space_type)
            for affected, percent in rig_impact.items():
                resulting_dict[affected] = percent

        for key in resulting_dict.keys():
            resulting_dict[key] -= citadel_impact
        return resulting_dict

    def te_mods(self):
        return {}

    def add_to_collection(self, prints: Iterable[BP]):
        names = [p.name for p in prints]
        diff = set(names) - set(importer.tables["types"]["typeName"])
        if diff:
            raise ValueError("Unknow typenames:{}".format(diff))
        self.collection.add(prints)

    def save_setup(self):
        with open("fetchlib/setups/main_setup.pkl", "wb") as f:
            pickle.dump(self, f)
