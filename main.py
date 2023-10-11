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
from fetchlib.static_data_export import sde
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


@app.get("/setup")
async def combine_setup(
    setup_id: int,
    setup_service: Annotated[SetupService, Depends(setup_service)],
    blueprint_service: Annotated[BlueprintService, Depends(blueprint_service)],
    rig_service: Annotated[MediumRigService, Depends(medium_rig_service)],
    citadel_service: Annotated[CitadelService, Depends(citadel_service)],
    non_productable_service: Annotated[
        NonProductableService, Depends(non_productable_service)
    ],
):
    # rigs = await rig_service.get_medium_rigs(setup_id)
    blueprints = await blueprint_service.get_blueprints(setup_id)
    # citadels = await citadel_service.get_citadels(setup_id)
    non_productables = await non_productable_service.get_non_productables(setup_id)
    # rigs = []
    # for citadel in citadels:
    # rigs += rig_service.get_medium_rigs(citadel["id"])

    partial_setup = await setup_service.get_setup(setup_id)

    partial_setup(non_productables=non_productables, blueprint_collection=blueprints)
    return {"status": 200, "msg": "Setup was succesfully created"}


@app.get("/production")
def evaluate_production():
    pass


@app.get("/medium_rigs")
def get_medium_rigs(
    setup_id: int,
    citadel_service: Annotated[CitadelService, Depends(citadel_service)],
    rig_service: Annotated[MediumRigService, Depends(medium_rig_service)],
) -> List[MediumRigSchema]:
    citadels = citadel_service.get_citadels(setup_id)
    return [
        rig
        for rig in medium_rig_service.get_medium_rigs(citadel["citadel_id"])
        for citadel in citadels
    ]


@app.post("/space")
def set_space():
    pass


@app.get("/blueprints")
async def get_blueprint(
    setup_id: int,
    blueprint_service: Annotated[BlueprintService, Depends(blueprint_service)],
):
    return await blueprint_service.get_blueprints(setup_id)


# @app.get("/lines")
# def get_lines_amount():
#     return {"reaction": setup.reaction_lines, "production": setup.production_lines}


@app.post("/lines")
def set_lines_amount():
    pass
