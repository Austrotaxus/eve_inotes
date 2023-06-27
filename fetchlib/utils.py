import os
from abc import abstractproperty
from collections import defaultdict
from pathlib import Path
from typing import List

PATH = (
    Path(os.path.expanduser("~")) / ".eve_db"
    if os.name != "nt"
    else Path("C:\\Programm Files") / "eve_db"
)


class BaseCollectionMixin:
    @classmethod
    def fields(cls):
        return list(cls.to_dict().keys())

    @classmethod
    def to_dict(cls):
        d = cls.__dict__
        return {k: v for k, v in d.items() if not k.startswith("__")}


class ProductionClass(BaseCollectionMixin):
    ADVANCED_CAPITAL_COMPONENT = "advanced_capital_component"
    ADVANCED_CAPITAL_SHIP = "advanced_capital_ship"
    ADVANCED_COMPONENT = "advanced_component"
    ADVANCED_LARGE_SHIP = "advanced_large_ship"
    ADVANCED_MEDIUM_SHIP = "advanced_medium_ship"
    ADVANCED_SMALL_SHIP = "advanced_small_ship"
    AMMO = "ammo"
    BASIC_CAPITAL_COMPONENT = "basic_capital_component"
    BASIC_CAPITAL_SHIP = "basic_capital_ship"
    BASIC_LARGE_SHIP = "basic_large_ship"
    BASIC_MEDIUM_SHIP = "basic_medium_ship"
    BASIC_SMALL_SHIP = "basic_small_ship"
    DRONE_OR_FIGHTER = "drone_or_fighter"
    STRUCTURE_OR_COMPONENT = "structure_component"


class ReactionClass(BaseCollectionMixin):
    HYBRID_REACTION = "hybrid_reactions"
    COMPOSITE_REACTION = "composite_reactions"
    BIOCHEMICAL_REACTION = "biochemical_reactions"


class CitadelType(BaseCollectionMixin):
    ASTRAHUS = "Astrahus"
    RAITARU = "Raitaru"
    ATHANOR = "Athanor"


class SpaceType(BaseCollectionMixin):
    HIGHSEC = "highsec"
    LOWSEC = "lowsec"
    NULL_WH = "null_wh"


"""
Impact of rig ingame is unclear and non-documented.
I didn't manage to find any data, so I've try to reproduce it
Approach is group_id base since it seems like items in one final group
obtain the same bonuses from rigs.
"""
# FIXME incomplete list
CLASSES_GROUPS = {
    ProductionClass.ADVANCED_COMPONENT: {
        "amarr_component": 802,
        "caldari_component": 803,
        "gallente_component": 1889,
        "minmatar_component": 1888,
        "sleeper_component": 1147,
        "ram": 1908,
        "fuel": 1870,  # FIXME need to check
        "protective_components": 2768,
    },
    ProductionClass.BASIC_CAPITAL_COMPONENT: {
        "basic_capital_component": 781,
    },
    ProductionClass.ADVANCED_CAPITAL_COMPONENT: {
        "advanced_amarr_capital_component": 1884,
        "advanced_caldari_capital_component": 1885,
        "advanced_gallente_capital_component": 1886,
        "advanced_minmatar_capital_component": 1887,
    },
    ProductionClass.BASIC_CAPITAL_SHIP: {},
    ProductionClass.ADVANCED_CAPITAL_SHIP: {},
    ProductionClass.STRUCTURE_OR_COMPONENT: {
        "structure_component": 1865,
        "engineering_complex": 2324,
        "standard_citadel": 2201,
        "refinery": 2327,
    },
    ProductionClass.BASIC_LARGE_SHIP: {
        "caldati_battleship": 80,
        "amarr_battleship": 79,
        "gallente_battleship": 81,
        "minmatar_battleship": 78,
        "precursor_battleship": 2429,
        "industrial_command_ship": 2335,  # FIXME need to check for porpoise
        "pirate_faction_battleship": 1380,
        "navy_faction_battleship": 1379,
    },
    ProductionClass.ADVANCED_LARGE_SHIP: {
        "amarr_black_ops": 1076,
        "amarr_maradeur": 1081,
        "caldari_black_ops": 1077,
        "caldari_maradeur": 1082,
        "gallente_black_ops": 1078,
        "gallente_maradeur": 1083,
        "minmatar_black_ops": 1079,
        "minmatar_maradeur": 1084,
    },
    ProductionClass.BASIC_MEDIUM_SHIP: {
        "amarr_battlecruiser": 470,
        "amarr_cruiser": 74,
        "caldati_battlecruiser": 4306,
        "caldati_cruiser": 75,
        "gallente_battlecruiser": 469,
        "gallente_cruiser": 76,
        "minmatar_battlecruiser": 473,
        "minmatar_cruiser": 73,
        "navy_faction_battlecruiser": 1704,
        "navy_faction_cruiser": 1370,
        "pirate_faction_cruiser": 1371,
        "precursor_battlecruiser": 2542,
        "precursor_cruiser": 2428,
    },
    ProductionClass.ADVANCED_MEDIUM_SHIP: {
        "amarr_command": 825,
        "amarr_heavy_assault_cruisers": 449,
        "amarr_heavy_interdictors": 1071,
        "amarr_logistics": 438,
        "amarr_recon": 827,
        "amarr_strategic": 1139,
        "amarr_sub_core": 1122,
        "amarr_sub_defensive": 1126,
        "amarr_sub_offensive": 1130,
        "amarr_sub_propulsion": 1134,
        "caldari_command": 828,
        "caldari_heavy_assault_cruisers": 450,
        "caldari_heavy_interdictors": 1072,
        "caldari_logistics": 439,
        "caldari_recon": 830,
        "caldari_strategic": 1140,
        "caldari_sub_core": 1123,
        "caldari_sub_defensive": 1127,
        "caldari_sub_offensive": 1131,
        "caldari_sub_propulsion": 1135,
        "exhumers": 874,
        "flag_cruisers": 2417,
        "gallente_command": 831,
        "gallente_heavy_assault_cruisers": 451,
        "gallente_heavy_interdictors": 1073,
        "gallente_logistics": 440,
        "gallente_recon": 833,
        "gallente_strategic": 1141,
        "gallente_sub_core": 1124,
        "gallente_sub_defensive": 1129,
        "gallente_sub_offensive": 1132,
        "gallente_sub_propulsion": 1136,
        "minmatar_command": 834,
        "minmatar_heavy_assault_cruisers": 452,
        "minmatar_heavy_interdictors": 1074,
        "minmatar_logistics": 441,
        "minmatar_recon": 836,
        "minmatar_strategic": 1142,
        "minmatar_sub_core": 1125,
        "minmatar_sub_defensive": 1128,
        "minmatar_sub_offensive": 1133,
        "minmatar_sub_propulsion": 1137,
        "triglavian_heavy_assault_cruisers": 2535,
        "triglavian_logistics": 2526,
    },
    ReactionClass.BIOCHEMICAL_REACTION: {
        "booster_material_reaction": 1858,
        "molecular_forged_material_reaction": 2767,
    },
    ReactionClass.COMPOSITE_REACTION: {
        "advanced_composite_reaction": 499,
        "processed_composite_reaction": 500,
    },
    ReactionClass.HYBRID_REACTION: {
        "hybrid_reaction": 1860,
    },
}
