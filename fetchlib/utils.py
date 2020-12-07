import json
from typing import Iterable

import pandas as pd


class BaseCollection:
    @classmethod
    def fields(cls):
        return list(cls.to_dict().keys())

    @classmethod
    def to_dict(cls):
        d = cls.__dict__
        return {k: v for k, v in d.items() if not k.startswith("__")}


class ProductionClasses(BaseCollection):
    ADVANCED_COMPONENT = "advanced_component"
    BASIC_CAPITAL_COMPONENT = "basic_capital_component"
    ADVANCED_CAPITAL_COMPONENT = "advanced_capital_component"
    STRUCTURE_COMPONENT = "structure_component"
    ADVANCED_CAPITAL_SHIP = "advanced_capital_ship"
    BASIC_CAPITAL_SHIP = "basic_capital_ship"
    ADVANCED_LARGE_SHIP = "advanced_large_ship"
    BASIC_LARGE_SHIP = "basic_large_ship"
    ADVANCED_MEDIUM_SHIP = "advanced_medium_ship"
    BASIC_MEDIUM_SHIP = "basic_medium_ship"
    ADVANCED_SMALL_SHIP = "advanced_small_ship"
    BASIC_SMALL_SHIP = "basic_small_ship"
    AMMO = "ammo"
    DRONE_OR_FIGHTER = "drone_or_fighter"


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
    def to_df(self, me_mods={}, te_mods={}):
        lst = self.prints.values()
        names = (p.name for p in lst)
        mes = (p.me * me_mods.get(p.p_type, 1.0) for p in lst)
        tes = (p.te * te_mods.get(p.p_type, 1.0) for p in lst)
        runs = (p.runs for p in lst)
        return pd.DataFrame(
            data={
                "productName": [*names],
                "me": [*mes],
                "te": [*tes],
                "run": [*runs],
            }
        )


# ids of groups in eve database
groups_ids = {
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
}


CLASSES_GROUPS = {
    ProductionClasses.ADVANCED_COMPONENT: [
        groups_ids["amarr"],
        groups_ids["caldari"],
        groups_ids["gallente"],
        groups_ids["minmatar"],
        groups_ids["ram"],
        groups_ids["sleeper"],
        groups_ids["fuel"],  # FIXME need to check
    ],
    ProductionClasses.BASIC_CAPITAL_COMPONENT: [
        groups_ids["basic_capital"],
    ],
    ProductionClasses.ADVANCED_CAPITAL_COMPONENT: [
        groups_ids["advanced_amarr_capital"],
        groups_ids["advanced_caldari_capital"],
        groups_ids["advanced_gallente_capital"],
        groups_ids["advanced_minmatar_capital"],
    ],
    ProductionClasses.STRUCTURE_COMPONENT: [groups_ids["structure"]],
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
    SpaceTypes.HIGHSEC: 1.0 - 0.02,
    SpaceTypes.LOWSEC: 1.0 - 0.02 * 1.9,
    SpaceTypes.NULL_WH: 1.0 - 0.02 * 2.1,
}

default_t2 = {}


class Rigs(BaseCollection):
    ADV_ME_COMP_1 = Rig(
        [ProductionClasses.ADVANCED_COMPONENT],
        impact={"me": default_t1},
        name="M-set advanced component ME t1",
    )
    ADV_ME_SMALL_1 = Rig(
        [ProductionClasses.ADVANCED_SMALL_SHIP],
        impact={"me": default_t1},
        name="M-set advanced small ship ME t1",
    )

    ADV_ME_MEDIUM_1 = Rig(
        [ProductionClasses.ADVANCED_MEDIUM_SHIP],
        impact={"me": default_t1},
        name="M-set advanced medium ship ME t1",
    )

    @classmethod
    def to_dict(cls):
        d = cls.__dict__
        return {v.name: v for k, v in d.items() if type(v) == Rig}
