import json
import os
from pathlib import Path
from typing import Iterable

import pandas as pd

PATH = (
    Path(os.path.expanduser("~")) / ".eve_db"
    if os.name != "nt"
    else Path("C:\\Programm Files")
)


class BaseCollection:
    @classmethod
    def fields(cls):
        return list(cls.to_dict().keys())

    @classmethod
    def to_dict(cls):
        d = cls.__dict__
        return {k: v for k, v in d.items() if not k.startswith("__")}


class ProductionClasses(BaseCollection):
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
    STRUCTURE_COMPONENT = "structure_component"


class ReactionClasses(BaseCollection):
    HYBRID_REACTION = "hybrid_reactions"
    COMPOSITE_REACTION = "composite_reactions"
    BIOCHEMICAL_REACTION = "biochemical_reactions"


class CitadelTypes(BaseCollection):
    ASTRAHUS = "Astrahus"
    RAITARU = "Raitaru"
    ATHANOR = "Athanor"


class SpaceTypes(BaseCollection):
    HIGHSEC = "highsec"
    LOWSEC = "lowsec"
    NULL_WH = "null_wh"


class BP:
    def __init__(
        self,
        name,
        me,
        te,
        p_type,
        runs=None,
    ):
        self.name = name
        self.me = me
        self.te = te
        self.runs = runs if runs else 2 ** 20
        self.p_type = p_type

    def __repr__(self):
        return str(
            {
                "name": self.name,
                "me": self.me,
                "te": self.te,
                "p_type": self.p_type,
                "runs": self.runs,
            }
        )


class BlueprintCollection:
    def __init__(self, prints: Iterable[BP]):
        self.prints = {p.name: p for p in prints}

    def __repr__(self):
        return str(list(self.prints.values()))

    def add(self, prints: Iterable[BP]):
        for p in prints:
            self.prints[p.name] = p

    # return dataframe with respects to efficiency
    def to_df(self, me_impact={}, te_impact={}):
        lst = self.prints.values()
        names = (p.name for p in lst)
        m_effs = ((1 - p.me) * me_impact.get(p.p_type, 1.0) for p in lst)
        t_effs = ((1 - p.te) * te_impact.get(p.p_type, 1.0) for p in lst)
        runs = (p.runs for p in lst)
        return pd.DataFrame(
            data={
                "productName": [*names],
                "me_impact": [*m_effs],
                "te_impact": [*t_effs],
                "run": [*runs],
            }
        )


# ids of groups in eve database
comp_gids = {
    "amarr": 802,
    "caldari": 803,
    "gallente": 1889,
    "minmatar": 1888,
    "sleeper": 1147,
    "ram": 1908,
    "basic_capital": 781,
    "advanced_amarr_capital": 1884,
    "advanced_caldari_capital": 1885,
    "advanced_gallente_capital": 1886,
    "advanced_minmatar_capital": 1887,
    "fuel": 1870,
    "structure": 1865,
    "advanced_composite_reaction": 499,
    "processed_composite_reaction": 500,
    "hybrid_reaction": 1860,
    "booster_material": 1858,
    "molecular_forged_material": 2767,
}

ship_gids = {}

CLASSES_GROUPS = {
    ProductionClasses.ADVANCED_COMPONENT: [
        comp_gids["amarr"],
        comp_gids["caldari"],
        comp_gids["gallente"],
        comp_gids["minmatar"],
        comp_gids["ram"],
        comp_gids["sleeper"],
        comp_gids["fuel"],  # FIXME need to check
    ],
    ProductionClasses.BASIC_CAPITAL_COMPONENT: [
        comp_gids["basic_capital"],
    ],
    ProductionClasses.ADVANCED_CAPITAL_COMPONENT: [
        comp_gids["advanced_amarr_capital"],
        comp_gids["advanced_caldari_capital"],
        comp_gids["advanced_gallente_capital"],
        comp_gids["advanced_minmatar_capital"],
    ],
    ProductionClasses.STRUCTURE_COMPONENT: [comp_gids["structure"]],
    ProductionClasses.BASIC_LARGE_SHIP: [
        78,
        79,
        80,
        81,
    ],
    ReactionClasses.BIOCHEMICAL_REACTION: [
        comp_gids["booster_material"],
        comp_gids["molecular_forged_material"],
    ],
    ReactionClasses.COMPOSITE_REACTION: [
        comp_gids["processed_composite_reaction"],
        comp_gids["advanced_composite_reaction"],
    ],
    ReactionClasses.HYBRID_REACTION: [comp_gids["hybrid_reaction"]],
}


class Rig:
    def __init__(self, affected, impact, name="undefined"):
        self.affected = affected
        self.impact = impact
        self.name = name

    def represent_te(self, space_type):
        pass

    def represent_me(self, space_type):
        try:
            res = {a: self.impact["me"][space_type] for a in self.affected}
        except KeyError:
            res = {a: 1.0 for a in self.affected}

        return res

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, Rig):
            return (
                self.affected == other.affected and self.impact == other.impact
            )
        return False


default_t1 = {
    SpaceTypes.HIGHSEC: 0.02,
    SpaceTypes.LOWSEC: 0.02 * 1.9,
    SpaceTypes.NULL_WH: 0.02 * 2.1,
}

default_t2 = {}


class Rigs(BaseCollection):
    @classmethod
    def to_dict(cls):
        d = cls.__dict__
        return {v.name: v for k, v in d.items() if type(v) == Rig}


production_classes_dict = ProductionClasses.to_dict()
me_m_set_rigs_dict = {}
for field, value in production_classes_dict.items():
    rig = Rig(
        affected=[value],
        impact={"me": default_t1},
        name="M-set {} ME t1".format(value),
    )
    setattr(Rigs, field + "_ME_t1", rig)
