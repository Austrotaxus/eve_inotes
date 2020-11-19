import pickle
from pathlib import Path

from fetchlib.importer import Importer
from fetchlib.utils import Collection, BP, ProductionClasses

importer = Importer()


class Setup:
    def __init__(
        self,
    ):
        self.citadel_type = None
        self.space_type = None
        self.rig_set = None
        self.skills = None
        self.collection = Collection(self.initial_collection())
        self._non_productables = {
            "Nitrogen Fuel Block Blueprint",
            "Hydrogen Fuel Block Blueprint",
            "Helium Fuel Block Blueprint",
            "Oxygen Fuel Block Blueprint",
            "R.A.M.- Starship Tech Blueprint",
        }

    def initial_collection(self):
        d = importer.component_by_classes
        for tp, lst in d.items():
            for name in lst:
                yield BP(name, 0.9, 0.8, p_type=tp)

    def non_productables(self):
        return self._non_productables

    def me_mods(self):
        return {
            ProductionClasses.ADVANCED_COMPONENT: 0.958,
            ProductionClasses.ADVANCED_MEDIUM_SHIP: 0.958,
            ProductionClasses.ADVANCED_SMALL_SHIP: 0.958,
            ProductionClasses.ADVANCED_CAPITAL_COMPONENT: 0.958,
            ProductionClasses.ADVANCED_CAPITAL_SHIP: 0.956,
            ProductionClasses.BASIC_CAPITAL_SHIP: 0.94,
            ProductionClasses.BASIC_LARGE_SHIP: 0.94,
            ProductionClasses.BASIC_CAPITAL_COMPONENT: 0.948,
        }

    def te_mods(self):
        return {}
