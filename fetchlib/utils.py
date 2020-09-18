import pandas as pd

class BPC():
    def __init__(self, name, me, te, p_type='component',runs=None, ):
        self.name = name
        self.me = me * efficiency_rigs[p_type]
        self.te = te
        self.runs = runs if runs else 2**20
    def __repr__(self):
        return str((self.name,self.me,self.te))

class Collection():
    def __init__(self,prints):
        self.prints = {
            p.name:p for p in prints
        }

    def to_dataframe(self):
        lst = self.prints.values()
        names = (p.name for p in lst)
        mes = (p.me for p in lst)
        tes = (p.te for p in lst)
        runs = (p.runs for p in lst)
        return pd.DataFrame(data={'productName':names,'me':mes,'te':tes, 'run':runs})

    def __repr__(self):
        return str(self.prints)


efficiency_rigs = {'component': 0.958, 'ship':1, 'capital_ship':0.97}

hecate_bpcs = [
    BPC('Hecate',0.99, 0.92,runs= 7, p_type='ship'),
    BPC('Optimized Nano-Engines',0.9,0.8),
    BPC('Fullerene Intercalated Sheets', 0.9,0.8),
    BPC('Electromechanical Interface Nexus', 0.9,0.8),
    BPC('Fulleroferrocene Power Conduits' , 0.9,0.8),
    BPC('Reconfigured Subspace Calibrator', 0.9,0.8),
    BPC('Self-Assembling Nanolattice', 0.9,0.8),
    BPC('Metallofullerene Plating', 0.9,0.8),
    BPC('R.A.M.- Starship Tech', 0.9,0.8),
    BPC('Warfare Computation Core', 0.9,0.8),
]

sabre_comp_names = [
    'Plasma Thruster',
    'Nanomechanical Microprocessor',
    'Fernite Carbide Composite Armor Plate',
    'Ladar Sensor Cluster',
    'Deflection Shield Emitter',
    'R.A.M.- Starship Tech',
    'Nuclear Reactor Unit',
    'Electrolytic Capacitor Unit',
]
sabre_bpcs = [BPC(name, 0.9,0.9, p_type='component') for name in sabre_comp_names]
sabre_bpcs.append(BPC('Sabre', 0.97, 0.92, runs = 5, p_type='ship'))
sabre_bpcs.append(BPC('Thrasher', 0.9, 0.8, p_type='capital_ship'))

anshar_comp_names = [
 'Capital Jump Drive',
 'Capital Fusion Reactor Unit',
 'Capital Ion Thruster',
 'Capital Crystalline Carbonide Armor Plate',
 'Capital Pulse Shield Emitter',
 'R.A.M.- Starship Tech',
 'Capital Oscillator Capacitor Unit',
 'Capital Magnetometric Sensor Cluster',
 'Capital Photon Microprocessor',
 'Capital Construction Parts', 
 'Capital Propulsion Engine',
 'Capital Armor Plates',
 'Capital Cargo Bay',
 ]
anshar_bpcs = [BPC(name, 0.9,0.9, p_type='component') for name in anshar_comp_names]
anshar_bpcs.append(BPC('Anshar', 0.95, 0.92, runs = 1, p_type='ship'))
anshar_bpcs.append(BPC('Obelisk', 0.9, 0.8, p_type='ship'))



NON_PRODUCTABLE = {
    'Nitrogen Fuel Block Blueprint',
    'Hydrogen Fuel Block Blueprint',
    'Helium Fuel Block Blueprint',
    'Oxygen Fuel Block Blueprint',
    'R.A.M.- Starship Tech Blueprint'
}
my_collection = Collection(hecate_bpcs+sabre_bpcs+anshar_bpcs)   