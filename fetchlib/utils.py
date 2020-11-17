import json
from typing import Iterable

import pandas as pd

NON_PRODUCTABLE = {
    "Nitrogen Fuel Block Blueprint",
    "Hydrogen Fuel Block Blueprint",
    "Helium Fuel Block Blueprint",
    "Oxygen Fuel Block Blueprint",
    "R.A.M.- Starship Tech Blueprint",
}


class Classes:
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
        self.me = me * efficiency_mods.get(p_type, 1.0)
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


class Collection:
    def __init__(self, prints: Iterable[BP]):
        self.prints = {p.name: p for p in prints}

    def __repr__(self):
        return str(list(self.prints.values()))

    def add(self, prints: Iterable[BP]):
        for p in prints:
            self.prints[p.name] = p

    def to_dataframe(self):
        lst = self.prints.values()
        names = (p.name for p in lst)
        mes = (p.me for p in lst)
        tes = (p.te for p in lst)
        runs = (p.runs for p in lst)
        return pd.DataFrame(
            data={
                "productName": [*names],
                "me": [*mes],
                "te": [*tes],
                "run": [*runs],
            }
        )


# Impact of overall setup: facility type + rig + environment
efficiency_mods = {
    Classes.ADVANCED_COMPONENT: 0.958,
    Classes.ADVANCED_MEDIUM_SHIP: 0.958,
    Classes.ADVANCED_SMALL_SHIP: 0.958,
    Classes.ADVANCED_CAPITAL_COMPONENT: 0.958,
    Classes.ADVANCED_CAPITAL_SHIP: 0.956,
    Classes.BASIC_CAPITAL_SHIP: 0.958,
    Classes.BASIC_LARGE_SHIP: 0.958,
    Classes.BASIC_CAPITAL_COMPONENT: 0.958,
}


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
    Classes.ADVANCED_COMPONENT: [
        groups_ids["amarr"],
        groups_ids["caldari"],
        groups_ids["gallente"],
        groups_ids["minmatar"],
        groups_ids["ram"],
        groups_ids["sleeper"],
        groups_ids["fuel"],  # FIXME need to check
    ],
    Classes.BASIC_CAPITAL_COMPONENT: [
        groups_ids["basic_capital"],
    ],
    Classes.ADVANCED_CAPITAL_COMPONENT: [
        groups_ids["advanced_amarr_capital"],
        groups_ids["advanced_caldari_capital"],
        groups_ids["advanced_gallente_capital"],
        groups_ids["advanced_minmatar_capital"],
    ],
    Classes.STRUCTURE_COMPONENT: [groups_ids["structure"]],
}


def components():
    with open("fetchlib/blueprints/components.json") as f:
        d = json.load(f)
    for tp, lst in d.items():
        for name in lst:
            yield BP(name, 0.9, 0.8, p_type=tp)


my_collection = Collection([*components()])
