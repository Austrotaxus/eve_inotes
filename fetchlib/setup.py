import pickle
from typing import Iterable, Set

import pandas as pd

from fetchlib.blueprint import Blueprint, BlueprintCollection
from fetchlib.rig import RigSet
from fetchlib.static_data_export import sde
from fetchlib.utils import PATH, CitadelType, ProductionClass, SpaceType

DEFAULT_NON_PRODUCTABLES = {
    "Nitrogen Fuel Block",
    "Oxygen Fuel Block",
    "Helium Fuel Block",
    "Hydrogen Fuel Block",
}


class Setup:
    """Represents industry cluster used for production."""

    # FIXME probably should apply 'builder' pattern
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
        self.reaction_lines = 20
        self.production_lines = 20
        self._non_productables = non_productables
        self.collection = BlueprintCollection(self.initial_collection())

    def initial_collection(self):
        data = sde.component_by_classes
        for product_type, lst in data.items():
            for name in lst:
                yield Blueprint(name, 0.1, 0.2)

    @property
    def non_productables(self) -> Set[str]:
        """
        Returns:
            Set of typeNames unwanted for production.
        """
        return self._non_productables

    def add_blueprint_to_collection(
        self,
        *,
        name: str,
        material_efficiency: float,
        time_efficiency: float,
        runs: int,
    ):
        """Add blueprint to inner blueprint collection.
        Args:
            name - produced typeName
            material_efficiency - me in [0.0, 0.1]
            time_efficiency - te in [0.0, 0.2]
            runs - max runs of blueprint
        """
        if not sde.types["typeName"].str.contains(name).any():
            raise ValueError(f"Unknown typename: {name}")
        self.collection.add(Blueprint(name=name, **kwargs))

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

    @property
    def efficiency_impact(self) -> pd.DataFrame:
        """
        Returns:
            pandas DataFrame indexed by typeName containing info
            about combined blueprint and rig impact. For example:
            -----------------------------------------------------
                    te_impact me_impact runs
            Raven        0.85      0.56  10
        """
        rig_df = self.rig_set.to_dataframe(self.space_type, sde)
        bp_df = self.collection.to_dataframe

        res = rig_df.join(bp_df, how="outer", rsuffix="_x", lsuffix="_y").fillna(1)
        res["te_impact"] = res["te_impact_x"] * res["te_impact_y"]
        res["me_impact"] = res["me_impact_x"] * res["me_impact_y"]

        return res[["te_impact", "me_impact", "run"]]


setup = Setup.load_setup() or Setup()
