from typing import Iterable

import pickle

from fetchlib.static_data_export import sde
from fetchlib.utils import (
    BlueprintCollection,
    Blueprint,
    ProductionClasses,
    SpaceTypes,
    CitadelTypes,
    PATH,
)


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
            "Nitrogen Fuel Block",
            "Oxygen Fuel Block",
            "Helium Fuel Block",
            "Hydrogen Fuel Block",
        }

    @classmethod
    def default_impact(cls):
        members = ProductionClasses.to_dict().values()
        res = {m: 1.0 for m in members}
        return res

    def initial_collection(self):
        d = sde.component_by_classes
        for tp, lst in d.items():
            for name in lst:
                yield Blueprint(name, 0.1, 0.2, product_type=tp)

    def non_productables(self):
        return self._non_productables

    def material_efficiency_impact(self):
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

    def time_efficiency_impact(self):
        return {}

    def add_blueprints_to_collection(self, prints: Iterable[Blueprint]):
        names = [p.name for p in prints]
        diff = set(names) - set(sde.types["typeName"])
        if diff:
            raise ValueError("Unknow typenames:{}".format(diff))
        self.collection.add(prints)

    def add_blueprint_to_collection(self, name, **kwargs):
        if not sde.types["typeName"].str.contains(name).any():
            raise ValueError(f"Unknown typename: {name}")
        self.collection.add_blueptint(name=name, **kwargs)

    def save_setup(self):
        with open(PATH / "main_setup.pkl", "wb") as f:
            pickle.dump(self, f)

    def set_lines_amount(self, reaction: int, production: int):
        self.reaction_lines = reaction
        self.production_lines = production


setup = Setup()
