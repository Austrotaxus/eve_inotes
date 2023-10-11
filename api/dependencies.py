from repository.repository import (
    BlueprintRepository,
    CitadelRepository,
    MediumRigRepository,
    NonProductableRepository,
    SetupRepository,
)
from service.service import (
    BlueprintService,
    CitadelService,
    MediumRigService,
    NonProductableService,
    SetupService,
)


def blueprint_service():
    return BlueprintService(BlueprintRepository)


def citadel_service():
    return CitadelService(CitadelRepository)


def medium_rig_service():
    return MediumRigService(MediumRigRepository)


def setup_service():
    return SetupService(SetupRepository)


def non_productable_service():
    return NonProductableService(NonProductableRepository)
