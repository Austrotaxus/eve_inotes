import json
from typing import Iterable

import pandas as pd

from fetchlib.importer import Importer

I = Importer()

NON_PRODUCTABLE = {
    "Nitrogen Fuel Block Blueprint",
    "Hydrogen Fuel Block Blueprint",
    "Helium Fuel Block Blueprint",
    "Oxygen Fuel Block Blueprint",
    "R.A.M.- Starship Tech Blueprint",
}

class Classes:
    ADVANCED_COMPONENT = 'advanced_component'
    BASIC_CAPITAL_COMPONENT = 'basic_capital_component'
    ADVANCED_CAPITAL_COMPONENT = 'advanced_capital_component'
    STRUCTURE_COMPONENT = 'structure_component'
    

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
        self.me = me * efficiency_rigs.get(p_type,1.0)
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
efficiency_rigs = {
    Classes.ADVANCED_COMPONENT: 0.958,
    "small_basic_ship": 1,
    "small_advanced_ship":1,
    "capital_basic_ship": 0.97,
    Classes.ADVANCED_CAPITAL_COMPONENT:0.958,
    'capital_advanced_ship':0.956}

def components():
    with open('fetchlib/blueprints/components.json') as f:
        d = json.load(f)
    for tp, lst in d.items():
        for name in lst:
            yield BP(name, 0.9,0.8,p_type=tp)


my_collection = Collection([*components()])

