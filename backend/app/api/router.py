from fastapi import APIRouter

from .endpoints import history, predict, system

router = APIRouter(prefix="/api/v1")
router.include_router(system.router)
router.include_router(predict.router)
router.include_router(history.router)
