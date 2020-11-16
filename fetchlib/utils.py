import json
from typing import Iterable

import pandas as pd

from fetchlib.importer import Importer


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
        p_type="component",
        runs=None,
    ):
        self.name = name
        self.me = me * efficiency_mods.get(p_type, 1.0)
        self.te = te
        self.runs = runs if runs else 2 ** 20

    def __repr__(self):
        return str((self.name, self.me, self.te))


class Collection:
    def __init__(self, prints: Iterable[BP]):
        self.prints = {p.name: p for p in prints}

    def __repr__(self):
        return str(self.prints)

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


def components():
    with open("fetchlib/blueprints/components.json") as f:
        d = json.load(f)
    for tp, lst in d.items():
        for name in lst:
            yield BP(name, 0.9, 0.8, p_type=tp)


my_collection = Collection([*components()])
