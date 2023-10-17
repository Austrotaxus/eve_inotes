from functools import partial
from typing import List

from fetchlib.blueprint import Blueprint, BlueprintCollection
from fetchlib.rig import MediumSetIndustryRig, RigSet
from fetchlib.setup import Setup
from repository.repository import AbstractRepository
from schema.schema import (
    BlueprintSchema,
    CitadelSchema,
    MediumRigSchema,
    NonProductableSchema,
    SetupSchema,
)


class SetupService:
    # Sould this prodvide a setup?
    def __init__(self, setup_repo: AbstractRepository):
        self.setup_repo: AbstractRepository = setup_repo()

    async def add_setup(self, setup: "Setup"):
        setup_dict = setup.model_dump()
        setup_id = await self.tasks_repo.add_one(setup_dict)
        return setup_id

    async def get_setups(self, user_id):
        pass

    async def get_setup(self, setup_id):
        setup_records = await self.setup_repo.find_all(setup_id=setup_id)
        if not setup_records:
            raise ValueError(f"No setup for given id:{setup_id}")

        payload = setup_records[0].model_dump()
        payload.pop("user_id")
        payload.pop("setup_id")
        payload.pop("setup_name")
        return partial(Setup, **payload)


class CitadelService:
    def __init__(self, citadel_repo: AbstractRepository):
        self.repo = citadel_repo()

    async def add_citadel(self, citadel: CitadelSchema):
        citadel_dict = citadel.model_dump()
        citadel_id = await self.repo.add_one(citadel_dict)
        return citadel_id

    async def get_citadels(self, setup_id):
        return await self.repo.find_all(setup_id=setup_id)


class BlueprintService:
    def __init__(self, blueprints_repo: AbstractRepository):
        self.blueprints_repo: AbstractRepository = blueprints_repo()

    async def add_blueprint(self, blueprint: "Blueprint"):
        blueprint_dict = blueprint.model_dump()
        blueprint_id = await self.blueprints_repo.add_one(blueprint_dict)
        return blueprint_id

    async def get_blueprint_collection(self, setup_id):
        blueprint_records = await self.blueprints_repo.find_all(setup_id)
        blueprints = [Blueprint(**record) for record in blueprint_records]
        return BlueprintCollection(blueprints)

    async def get_blueprints(self, setup_id):
        return await self.blueprints_repo.find_all(setup_id)


class MediumRigService:
    def __init__(self, medium_rig_repo: AbstractRepository):
        self.repo = medium_rig_repo()

    async def add_medium_rig(self, rig: MediumRigSchema):
        rig_dict = rig.model_dump()
        rig_id = await self.repo.add_one(rig_dict)
        return rig_id

    async def get_medium_rig_set(self, citadel_id) -> RigSet:
        rig_records = await self.repo.find_all(citadel_id)
        rigs = [MediumSetIndustryRig(**record) for record in rig_records]
        return RigSet(rigs)

    async def get_medium_rigs(self, citadel_id) -> List[MediumRigSchema]:
        return await self.repo.fild_all(citadel_id)


class NonProductableService:
    def __init__(self, nonproductables_repo: AbstractRepository):
        self.repo = nonproductables_repo()

    async def add_non_productable(self, non_productabe: NonProductableSchema):
        non_productabe_dict = non_productabe.model_dump()

        # Check if non productable is an eve item

        non_productable_id = await self.repo.add_one(non_productabe_dict)
        return non_productable_id

    async def get_non_productable_stirngs(self, setup_id):
        non_productable_records = await self.repo.find_all(setup_id)
        non_productables = [
            record["non_productable"] for record in non_productable_records
        ]
        return non_productables

    async def get_non_productables(self, setup_id) -> List[NonProductableSchema]:
        return await self.repo.find_all(setup_id)
