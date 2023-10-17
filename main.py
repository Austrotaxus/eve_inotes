from typing import Annotated, List

from fastapi import Depends, FastAPI

from api.dependencies import (
    blueprint_service,
    citadel_service,
    medium_rig_service,
    non_productable_service,
    setup_service,
)
from fetchlib import balancify_runs
from fetchlib.decomposition import Decomposition
from fetchlib.decompositor import Decompositor
from fetchlib.rig import AVALIABLE_RIGS, RigSet
from fetchlib.setup import Setup
from fetchlib.static_data_export import StaticDataExport
from fetchlib.utils import CitadelType, ProductionClass, SpaceType
from schema.schema import (
    BlueprintSchema,
    CitadelSchema,
    MediumRigSchema,
    NonProductableSchema,
    SetupSchema,
)
from service.service import (
    BlueprintService,
    CitadelService,
    MediumRigService,
    NonProductableService,
    SetupService,
)

app = FastAPI()


async def combine_rigs(setup_id: int) -> RigSet:
    citadels = await citadel_service().get_citadels(setup_id)

    return RigSet(
        [rig_service().get_rig_set(citadel.citadel_id) for citadel in citadels]
    )


async def combine_setup(
    setup_id: int,
):
    rigs = await combine_rigs(setup_id)
    # citadel_service = citadel_service()
    blueprints = await blueprint_service().get_blueprints(setup_id)
    non_productables = await non_productable_service().get_non_productables(setup_id)
    partial_setup = await setup_service().get_setup(setup_id)

    setup = partial_setup(
        non_productables=non_productables,
        blueprint_collection=blueprints,
        rig_set=rigs,
    )
    return setup


@app.get("/production")
async def evaluate_production(
    setup_id: int,
    product: str,
    quantity: int,
) -> str:
    setup = await combine_setup(setup_id=setup_id)
    sde = StaticDataExport()
    table = sde.create_init_table(**{product: quantity})
    decompositor_function = Decompositor(sde, setup)
    decomposition = Decomposition(step=table, decompositor=decompositor_function)
    return str(decomposition)
