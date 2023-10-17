from enum import Enum

from pydantic import BaseModel, Field

from fetchlib.utils import CitadelType, ProductionClass, RigType, SpaceType, Tier


class SetupSchema(BaseModel):
    setup_id: int
    user_id: int
    reaction_lines: int = Field(ge=0)
    production_lines: int = Field(ge=0)
    setup_name: str


class MediumRigSchema(BaseModel):
    rig_type: str
    citadel_id: int
    tier: Tier
    rig_type: RigType
    production_class: ProductionClass


class BlueprintSchema(BaseModel):
    blueprint_id: int
    product: str
    material_efficiency: float = Field(ge=0, le=0.1)
    time_efficiency: float = Field(ge=0, le=0.2)
    runs: int = Field(ge=0)


class CitadelSchema(BaseModel):
    citadel_id: int
    setup_id: int
    space_type: SpaceType
    citadel_type: CitadelType


class NonProductableSchema(BaseModel):
    setup_id: int
    non_productable: str
