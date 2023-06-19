import pickle
from typing import Iterable

from fetchlib.static_data_export import sde
from fetchlib.utils import (
    Blueprint,
    BlueprintCollection,
    CitadelType,
    PATH,
    ProductionClass,
    RigSet,
    SpaceType,
)


DEFAULT_NON_PRODUCTABLES = {
    "Nitrogen Fuel Block",
    "Oxygen Fuel Block",
    "Helium Fuel Block",
    "Hydrogen Fuel Block",
}


class Setup:
    def __init__(
        self,
        path=PATH / "main_setup.pkl",
        non_productables=DEFAULT_NON_PRODUCTABLES,
        reaction_lines=20,
        production_lines=20,
    ):
        self.path = path
        self.citadel_type = CitadelType.RAITARU
        self.space_type = SpaceType.NULL_WH
        self.rig_set = RigSet()
        self.skills = None
        self.collection = BlueprintCollection(self.initial_collection())
        self.reaction_lines = 20
        self.production_lines = 20
        self._non_productables = non_productables

    @classmethod
    def default_impact(cls):
        members = ProductionClass.to_dict().values()
        res = {m: 1.0 for m in members}
        return res

    def initial_collection(self):
        d = sde.component_by_classes
        for product_type, lst in d.items():
            for name in lst:
                yield Blueprint(name, 0.1, 0.2, product_type=product_type)

    def non_productables(self):
        return self._non_productables

    def material_efficiency_impact(self):
        citadel_impact = 1 - (
            (self.citadel_type in (CitadelType.RAITARU,)) * 0.01
        )

        impact_dict = {}
        rig_impact_dict = self.rig_set.represent_me(self.space_type)
        for production_class, rig_impact in rig_impact_dict.items():
            for product_type in sde.get_class_contents(
                production_class=production_class
            ):
                impact_dict[product_type] = 1.0 - rig_impact

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
        with open(self.path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load_setup(cls, path=PATH / "main_setup.pkl"):
        if path.exists():
            with open(path, "rb") as file:
                return pickle.load(file)
        return None

    def set_lines_amount(self, reaction: int, production: int):
        self.reaction_lines = reaction
        self.production_lines = production


setup = Setup.load_setup() or Setup()
