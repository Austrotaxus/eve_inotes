import enum

from sqlalchemy import Column, Enum, Float, ForeignKey, Integer, MetaData, String
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

from db.db import Base
from fetchlib.utils import CitadelType, ProductionClass, RigType, SpaceType, Tier
from schema.schema import (
    BlueprintSchema,
    CitadelSchema,
    MediumRigSchema,
    NonProductableSchema,
    SetupSchema,
)


class Setup(Base):
    __tablename__ = "setup"
    setup_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    reaction_lines = mapped_column(Integer, nullable=False)
    production_lines = mapped_column(Integer, nullable=False)

    def to_read_model(self) -> SetupSchema:
        return SetupSchema(
            setup_id=self.setup_id,
            user_id=0,
            reaction_lines=self.reaction_lines,
            production_lines=self.production_lines,
        )


class Citadel(Base):
    __tablename__ = "citadel"
    citadel_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    setup_id = mapped_column(ForeignKey("setup.setup_id"), nullable=False)
    citadel_type = mapped_column(Enum(CitadelType))
    space_type = mapped_column(Enum(SpaceType))

    def to_read_model(self) -> CitadelSchema:
        return CitadelSchema(
            citadel_id=self.citadel_id,
            setup_id=self.setup_id,
            citadel_type=self.citadel_type,
            space_type=self.space_type,
        )


class MediumRig(Base):
    __tablename__ = "medium_rig"
    rig_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    tier = mapped_column(Enum(Tier), nullable=False)
    citadel_id = mapped_column(ForeignKey("citadel.citadel_id"), nullable=False)
    setup_id = mapped_column(ForeignKey("setup.setup_id"), nullable=False)
    rig_type = mapped_column(Enum(RigType))
    production_class = mapped_column(Enum(ProductionClass))


class User(Base):
    __tablename__ = "user"
    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    setup_id = mapped_column(ForeignKey("setup.setup_id"), nullable=False)


class Blueprint(Base):
    __tablename__ = "blueprint"
    blueprint_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    setup_id = mapped_column(ForeignKey("setup.setup_id"), nullable=False)
    material_efficiency = mapped_column(Float, nullable=False)
    time_efficiency = mapped_column(Float, nullable=False)
    runs = mapped_column(Integer, default=2**20)
    blueprint = mapped_column(String, nullable=False)

    def to_read_model(self) -> BlueprintSchema:
        return BlueprintSchema(
            setup_id=self.setup_id,
            blueprint_id=self.blueprint_id,
            blueprint="Some blueprint",
            material_efficiency=self.material_efficiency,
            time_efficiency=self.time_efficiency,
            runs=self.runs,
        )


class NonProductable(Base):
    __tablename__ = "nonproductable"
    nonproductable_id = mapped_column(Integer, primary_key=True, autoincrement=True)
    setup_id = mapped_column(ForeignKey("setup.setup_id"), nullable=False)
