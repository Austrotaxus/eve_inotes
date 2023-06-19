import pandas as pd
import pytest

from fetchlib.static_data_export import AbstractDataExport, sde
from fetchlib.utils import ProductionClass

types_columns = ["typeID", "groupID", "typeName", "marketGroupID"]
product_columns = ["typeID", "activityID", "productTypeID", "quantity"]
materials_columns = ["typeID", "activityID", "materialTypeID", "quantity"]
activities_columns = ["typeID", "activityID", "time"]
market_group_columns = [
    "marketGroupID",
    "parentGroupID",
    "marketGroupName",
    "description",
    "iconID",
    "hasTypes",
]


class FakeDataExport(AbstractDataExport):
    @property
    def types(self):
        data = [
            (29984, 963, "Tengu", 1140.0),
            (29985, 996, "Tengu Blueprint", None),
            (45653, 964, "Superconducting Gravimetric Amplifier", 1147.0),
            (
                45657,
                965,
                "Superconducting Gravimetric Amplifier Blueprint",
                1191.0,
            ),
            (30303, 974, "Fulleroferrocene", 1860.0),
            (46158, 1889, "Fulleroferrocene Reaction Formula", 2404.0),
            (30371, 711, "Fullerite-C60", 1859.0),
        ]
        return pd.DataFrame.from_records(data, columns=types_columns)

    @property
    def products(self):
        data = [
            (29985, 1, 29984, 1),  # Tengu blueprint
            (45657, 1, 45653, 1),  # Superconducting Gravimetric Amplifier
            (46158, 11, 30303, 1000),  # Fulleroferrocene Reaction Formula
        ]
        return pd.DataFrame.from_records(data, columns=product_columns)

    @property
    def materials(self):
        data = [
            (29985, 1, 45653, 12),  # SGA for Tengu
            (46158, 11, 30371, 100),  # Fulleroferrocene for SGA
        ]
        return pd.DataFrame.from_records(data, columns=materials_columns)

    @property
    def activities(self):
        data = [
            (29985, 1, 300000),  # Tengu blueprint
            (45657, 1, 600),  # SGA blueprint
            (46158, 11, 10800),  # Fulleroferrocene reaction formula
        ]
        return pd.DataFrame.from_records(data, columns=activities_columns)

    @property
    def market_groups(self):
        data = [
            (
                1140,
                1138.0,
                "Caldari",
                "Caldari strategic cruiser designs.",
                20966.0,
                1,
            ),
            (
                1147,
                1035.0,
                "Subsystem Components",
                "The building blocks of advanced subsystems.",
                3721.0,
                1,
            ),
            (
                1191,
                800.0,
                "Subsystem Components",
                "Blueprints of Subsystem Components.",
                2703.0,
                1,
            ),
            (
                1860,
                1034.0,
                "Polymer Materials",
                "Material made from combining fullerenes.",
                3751.0,
                1,
            ),
            (
                2404,
                1849.0,
                "Polymer Reaction Formulas",
                "Reaction formulas that enable the creation of Tech 3 construction materials in Refineries",
                21783.0,
                1,
            ),
            (
                1859,
                1032.0,
                "Fullerenes",
                "This rare form of gas can only be harvested in wormhole space.",
                3222.0,
                1,
            ),
        ]
        return pd.DataFrame.from_records(data, columns=market_group_columns)


fde = FakeDataExport()


@pytest.mark.parametrize("data_export", [fde, sde])
def test_sde_has_columns(data_export):
    assert not set(materials_columns) - set(data_export.materials.columns)

    assert not set(types_columns) - set(data_export.types.columns)

    assert not set(activities_columns) - set(data_export.activities.columns)

    assert not set(market_group_columns) - set(data_export.market_groups.columns)
    assert not set(product_columns) - set(data_export.products.columns)


@pytest.mark.parametrize("data_export", [fde, sde])
def test_product_results_are_unique(data_export):
    """Important requirement needed for Decompositor to work correctly"""
    assert data_export.products["productTypeID"].is_unique


@pytest.mark.parametrize("data_export", [fde, sde])
def test_preapare_init_talbe(data_export):
    table = data_export.create_init_table(Tengu=20)
    assert list(table.columns) == [
        "typeName",
        "quantity",
        "runs_required",
        "activityID",
        "typeID",
    ]
    assert table.shape[0] == 1


@pytest.mark.parametrize("data_export", [fde, sde])
def test_only_reaction_and_production(data_export):
    assert set(data_export.materials["activityID"].unique()) == set([1, 11])
    assert set(data_export.products["activityID"].unique()) == set([1, 11])
    assert set(data_export.activities["activityID"].unique()) == set([1, 11])


@pytest.mark.parametrize("data_export", [fde, sde])
def test_append_everything(data_export):
    """
    Chech if we get correct amount of records on expansion
    """

    table = data_export.create_init_table(Tengu=20)
    appended = data_export.append_everything(table)
    tengu_blueprint_id = data_export.types[
        data_export.types["typeName"] == "Tengu Blueprint"
    ]["typeID"].iloc[0]

    materials = data_export.materials

    assert (
        appended.shape[0]
        == materials[materials["typeID"] == tengu_blueprint_id].shape[0]
    )


@pytest.mark.parametrize("data_export", [fde, sde])
def test_get_class_contents(data_export):
    components = data_export.get_class_contents(ProductionClass.ADVANCED_COMPONENT)
    assert "Superconducting Gravimetric Amplifier" in components
