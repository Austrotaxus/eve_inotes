import json

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
    def __init__(self, prints):
        self.prints = {p.name: p for p in prints}

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

    def __repr__(self):
        return str(self.prints)


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

hecate_bpcs = [
    BP("Hecate", 0.99, 0.92, runs=7, p_type="small_advanced_ship"),
]

sabre_bpcs = []
sabre_bpcs.append(BP("Sabre", 0.97, 0.92, runs=5, p_type="small_advanced_ship"))
sabre_bpcs.append(BP("Thrasher", 0.9, 0.8, p_type="small_basic_ship"))

anshar_bpcs = []
anshar_bpcs.append(BP("Anshar", 0.95, 0.92, runs=1, p_type="capital_advanced_ship"))
anshar_bpcs.append(BP("Obelisk", 0.9, 0.8, p_type="capital_basic_ship"))




my_collection = Collection(hecate_bpcs + sabre_bpcs + anshar_bpcs + [*components()])
