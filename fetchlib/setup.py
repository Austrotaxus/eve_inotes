import pickle
from typing import Iterable, Optional, Set

import pandas as pd

from fetchlib.blueprint import Blueprint, BlueprintCollection
from fetchlib.rig import RigSet
from fetchlib.static_data_export import AbstractDataExport, sde
from fetchlib.utils import PATH, CitadelType, ProductionClass, SpaceType

DEFAULT_NON_PRODUCTABLES = {
    "Nitrogen Fuel Block",
    "Oxygen Fuel Block",
    "Helium Fuel Block",
    "Hydrogen Fuel Block",
}


class Setup:
    """Represents industry cluster used for production."""

    def __init__(
        self,
        citatedl_type=CitadelType.RAITARU,
        space_type=SpaceType.NULL_WH,
        rig_set=None,
        reaction_lines=20,
        production_lines=20,
        non_productables=DEFAULT_NON_PRODUCTABLES,
        blueprint_collection=None,
    ):
        """
        Args:
            path - file for setup serialization
        """
        self.citadel_type = citatedl_type
        self.space_type = space_type
        self.rig_set = rig_set if rig_set else RigSet()
        self.reaction_lines = reaction_lines
        self.production_lines = production_lines
        self._non_productables = (
            non_productables if non_productables else DEFAULT_NON_PRODUCTABLES
        )
        self.collection = (
            blueprint_collection if blueprint_collection else BlueprintCollection([])
        )

    @property
    def non_productables(self) -> Set[str]:
        """
        Returns:
            Set of typeNames unwanted for production.
        """
        # FIXME add reactions to non_productubles if spaceType is highsec or there is no refinery in citadels
        return self._non_productables

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


class SetupManager:
    """Class, responsible for Setup creation/serealization/management"""

    def __init__(self, data_export: AbstractDataExport):
        self.data_export = data_export

    def get(self, name: str) -> Setup:
        """Retrieves setup from storage or returns the new one and set's data_export field"""
        path = PATH / f"{name}_setup.pkl"
        if (setup := self.load_setup(path)) is not None:
            return setup
        setup = Setup(path)
        setup.collection = self.initial_collection
        return setup

    def load_setup(self, path) -> Optional[Setup]:
        """
        Args:
            path - file to find serialized object
        Returns:
            setup if exists, otherwise None
        """
        if path.exists():
            with open(path, "rb") as file:
                setup = pickle.load(file)
                return setup
        return None

    def save_setup(self, setup):
        """Saves setup to the storage."""
        with open(setup.path, "wb") as f:
            pickle.dump(setup, f)

    @property
    def initial_collection(self) -> BlueprintCollection:
        """Provides collection of component blueprints which
        are typically are originals and fully researched.
        """

        production_classes = [
            ProductionClass.ADVANCED_COMPONENT,
            ProductionClass.ADVANCED_CAPITAL_COMPONENT,
            ProductionClass.STRUCTURE_OR_COMPONENT,
        ]

        blueprints = [
            Blueprint(type_name, material_efficiency=0.1, time_efficiency=0.2)
            for production_class in production_classes
            for type_name in self.data_export.get_class_contents(production_class)
        ]

        return BlueprintCollection(blueprints)

    def add_blueprint_to_setup(self, setup, *, name, **kwargs):
        """Add blueprint to blueprint collection of setup.
        Args:
            name - produced typeName
            material_efficiency - me in [0.0, 0.1]
            time_efficiency - te in [0.0, 0.2]
            runs - max runs of blueprint
        """

        if name not in self.data_export.productable_type_names.values:
            raise ValueError(f"Unknown typename: {name}")

        setup.collection.add(Blueprint(name=name, **kwargs))

    def set_lines_amount(
        self,
        *,
        setup: Setup,
        reaction_lines: Optional[int],
        production_lines: Optional[int],
    ):
        if reaction is not None:
            self.reaction_lines = reaction_lines
        if production is not None:
            self.production_lines = production_lines

    def add_non_productable_to_setup(self, setup, name):
        if name not in self.data_export.productable_type_names.values:
            raise ValueError(f"Unknown typename: {name}")
        setup._non_productables.add(name)
