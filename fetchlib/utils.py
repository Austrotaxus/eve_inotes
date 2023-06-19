import os
from abc import abstractproperty
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List

import pandas as pd

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


@dataclass
class Blueprint:
    name: str
    material_efficiency: float
    time_efficiency: float
    runs: int = field(default=2**20)


class BlueprintCollection:
    def __init__(self, prints: Iterable[Blueprint]):
        self.prints = {blueprint.name: blueprint for blueprint in prints}

    def __repr__(self):
        return str(list(self.prints.values()))

    def add(self, prints: Iterable[Blueprint]):
        for blueprints in prints:
            self.prints[blueprints.name] = blueprints

    def add_blueptint(self, **kwargs):
        self.prints[kwargs["name"]] = Blueprint(**kwargs)

    # return dataframe with respects to efficiency
    def effective_dataframe(self, material_impact={}, time_impact={}):
        """
        Calculates effective time and material efficiency
        params:
        material_impact - dict of material impacts provided by setup (rigs+citadels)
        time_impact - dict of time impacts provided by setup (rigs+citadels)
        """
        blueprints = self.prints.values()
        names = (blueprint.name for blueprint in blueprints)
        material_efficiencies = (
            (1 - blueprint.material_efficiency)
            * material_impact.get(blueprint.name, 1.0)
            for blueprint in blueprints
        )
        time_efficiencies = (
            (1 - p.time_efficiency) * time_impact.get(p.product_type, 1.0)
            for p in blueprints
        )
        runs = (blueprint.runs for blueprint in blueprints)
        return pd.DataFrame(
            data={
                "productName": names,
                "me_impact": material_efficiencies,
                "te_impact": time_efficiencies,
                "run": runs,
            }
        )


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
        "caldari_command": 828,
        "caldari_heavy_assault_cruisers": 450,
        "caldari_heavy_interdictors": 1072,
        "caldari_logistics": 439,
        "caldari_recon": 830,
        "caldari_strategic": 1140,
        "flag_cruisers": 2417,
        "gallente_command": 831,
        "gallente_heavy_assault_cruisers": 451,
        "gallente_heavy_interdictors": 1073,
        "gallente_logistics": 440,
        "gallente_recon": 833,
        "gallente_strategic": 1141,
        "minmatar_command": 834,
        "minmatar_heavy_assault_cruisers": 452,
        "minmatar_heavy_interdictors": 1074,
        "minmatar_logistics": 441,
        "minmatar_recon": 836,
        "minmatar_strategic": 1142,
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


DEFAULT_T1_ME_IMPACT = {
    SpaceType.HIGHSEC: 0.02 * 1,
    SpaceType.LOWSEC: 0.02 * 1.9,
    SpaceType.NULL_WH: 0.02 * 2.1,
}

DEFAULT_T2_ME_IMPACT = {
    SpaceType.HIGHSEC: 0.024,
    SpaceType.LOWSEC: 0.024 * 1.9,
    SpaceType.NULL_WH: 0.024 * 2.1,
}

ME_IMPACTS = {1: DEFAULT_T1_ME_IMPACT, 2: DEFAULT_T2_ME_IMPACT}


class RigEffect:
    def __init__(self, tiel=1):
        self.tier = tier

    @abstractproperty
    def affects(self):
        ...

    def me_impact(self, space_type):
        ...

    def te_impact(self, space_type):
        ...

    def represent_te(self, space_type):
        res = {
            production_class: self.te_impact(space_type)
            for production_class in self.affects
        }
        return res

    def represent_me(self, space_type):
        res = {
            production_class: self.me_impact(space_type)
            for production_class in self.affects
        }
        return res


class MediumSetIndustryRig(RigEffect):
    def __init__(self, production_class, tier: int, rig_type: str = "ME"):
        assert rig_type in ("ME", "TE")
        assert tier in (1, 2)

        self.production_class = production_class
        self.tier = tier
        self.rig_type = rig_type

    @property
    def affects(self):
        return [self.production_class]

    def te_impact(self, space_type):
        return 0 if self.rig_type == "ME" else 0

    def me_impact(self, space_type):
        return (
            ME_IMPACTS[self.tier][space_type] if self.rig_type == "ME" else 0
        )

    def __repr__(self):
        return f"MSet t{self.tier} {self.production_class} {self.rig_type}"

    def __eq__(self, o):
        return (
            type(self) == type(o)
            and self.production_class == o.production_class
            and self.tier == o.tier
            and self.rig_type == o.rig_type
        )


AVALIABLE_RIGS = (
    MediumSetIndustryRig(
        production_class=ProductionClass.BASIC_LARGE_SHIP, tier=1
    ),
    MediumSetIndustryRig(
        production_class=ProductionClass.ADVANCED_LARGE_SHIP, tier=1
    ),
    MediumSetIndustryRig(
        production_class=ProductionClass.STRUCTURE_OR_COMPONENT, tier=1
    ),
    MediumSetIndustryRig(
        production_class=ProductionClass.BASIC_MEDIUM_SHIP, tier=1
    ),
    MediumSetIndustryRig(
        production_class=ProductionClass.ADVANCED_MEDIUM_SHIP, tier=1
    ),
    MediumSetIndustryRig(
        production_class=ProductionClass.ADVANCED_COMPONENT, tier=1
    ),
)


class RigSet(BaseCollectionMixin):
    def __init__(self, rig_effects: List[RigEffect] = None):
        self.rig_effects = rig_effects or []

    def represent_me(self, space_type):
        res = defaultdict(lambda: 0)
        for rig_effect in self.rig_effects:
            for production_class, modifier in rig_effect.represent_me(
                space_type
            ).items():
                res[production_class] = max(res[production_class], modifier)

        return res

    def represent_te(self, space_type):
        res = defaultdict(lambda: 0)
        for rig_effect in self.rig_effects:
            for group_id, modifier in rig_effect.represent_te(space_type):
                res[group_id] = max(res[group_id], modifier)

        return res

    def append(self, rig_effect):
        self.rig_effect.append(rig_effect)

    def __contains__(self, rig_effect):
        return rig_effect in self.rig_effects

    def __iter__(self):
        return iter(self.rig_effects)
