import pandas as pd

from fetchlib.rig import MediumSetIndustryRig, RigSet
from fetchlib.utils import ProductionClass, SpaceType

from .test_static_data_export import fde


def test_rig_effects_do_not_sum():
    t1 = MediumSetIndustryRig(
        production_class=ProductionClass.ADVANCED_MEDIUM_SHIP, tier=1
    )
    t2 = MediumSetIndustryRig(
        production_class=ProductionClass.ADVANCED_MEDIUM_SHIP, tier=2
    )

    rig_set = RigSet([t1, t2])
    assert rig_set.represent_me(SpaceType.NULL_WH) == t2.represent_me(SpaceType.NULL_WH)


def test_to_dataframe():
    """
    df.to_dataframe shoul return df like this
    Superconducting Gravimetric Amplifier       1.00      0.958
    Tengu                                       0.58      1.000
    """
    te = MediumSetIndustryRig(
        production_class=ProductionClass.ADVANCED_MEDIUM_SHIP, tier=1, rig_type="TE"
    )
    me = MediumSetIndustryRig(
        production_class=ProductionClass.ADVANCED_COMPONENT, tier=1, rig_type="ME"
    )
    rig_set = RigSet([me, te])

    df = rig_set.to_dataframe(space_type=SpaceType.NULL_WH, data_export=fde)
    expected = pd.DataFrame(
        data={"te_impact": [1.00, 0.58], "me_impact": [0.958, 1.00]},
        index=["Superconducting Gravimetric Amplifier", "Tengu"],
    )

    assert df.equals(expected)
