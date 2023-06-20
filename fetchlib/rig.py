from abc import ABC, abstractproperty
from collections import defaultdict
from typing import List

import pandas as pd

from fetchlib.utils import ProductionClass, ReactionClass, SpaceType

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

DEFAULT_T1_TE_IMPACT = {
    SpaceType.HIGHSEC: 0.2,
    SpaceType.LOWSEC: 0.2 * 1.9,
    SpaceType.NULL_WH: 0.2 * 2.1,
}

DEFAULT_T2_TE_IMPACT = {
    SpaceType.HIGHSEC: 0.24,
    SpaceType.LOWSEC: 0.24 * 1.9,
    SpaceType.NULL_WH: 0.24 * 2.1,
}

ME_IMPACTS = {1: DEFAULT_T1_ME_IMPACT, 2: DEFAULT_T2_ME_IMPACT}
TE_IMPACTS = {1: DEFAULT_T1_TE_IMPACT, 2: DEFAULT_T2_TE_IMPACT}


class RigEffect(ABC):
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
        return TE_IMPACTS[self.tier][space_type] if self.rig_type == "TE" else 0

    def me_impact(self, space_type):
        return ME_IMPACTS[self.tier][space_type] if self.rig_type == "ME" else 0

    def __repr__(self):
        return f"MSet t{self.tier} {self.production_class} {self.rig_type}"

    def __eq__(self, o):
        return (
            type(self) == type(o)
            and self.production_class == o.production_class
            and self.tier == o.tier
            and self.rig_type == o.rig_type
        )


class RigSet:
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
            for production_class, modifier in rig_effect.represent_te(
                space_type
            ).items():
                res[production_class] = max(res[production_class], modifier)

        return res

    def add(self, *rig_effects):
        self.rig_effects.extend(rig_effects)

    def __contains__(self, rig_effect):
        return rig_effect in self.rig_effects

    def __iter__(self):
        return iter(self.rig_effects)

    def to_dataframe(self, space_type, sde):
        me_dictionary = {
            typename: [1 - impact]
            for production_class, impact in self.represent_me(space_type).items()
            for typename in sde.get_class_contents(production_class)
        }
        te_dictionary = {
            typename: [1 - impact]
            for production_class, impact in self.represent_te(space_type).items()
            for typename in sde.get_class_contents(production_class)
        }
        me_df = pd.DataFrame.from_dict(
            me_dictionary, orient="index", columns=["me_impact"]
        )
        te_df = pd.DataFrame.from_dict(
            te_dictionary, orient="index", columns=["te_impact"]
        )
        return te_df.join(me_df, how="outer").fillna(1.0)


AVALIABLE_RIGS = (
    MediumSetIndustryRig(production_class=ProductionClass.BASIC_LARGE_SHIP, tier=1),
    MediumSetIndustryRig(production_class=ProductionClass.ADVANCED_LARGE_SHIP, tier=1),
    MediumSetIndustryRig(
        production_class=ProductionClass.STRUCTURE_OR_COMPONENT, tier=1
    ),
    MediumSetIndustryRig(production_class=ProductionClass.BASIC_MEDIUM_SHIP, tier=1),
    MediumSetIndustryRig(production_class=ProductionClass.ADVANCED_MEDIUM_SHIP, tier=1),
    MediumSetIndustryRig(production_class=ProductionClass.ADVANCED_COMPONENT, tier=1),
)
