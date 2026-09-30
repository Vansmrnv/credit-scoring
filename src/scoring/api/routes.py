from fastapi import APIRouter, HTTPException, Request

from ..core.engine import Engine
from ..db.repository import ApplicationStore
from ..schemas.schemas import CreditApplication, ScoringResult


def create_router(engine: Engine) -> APIRouter:
    router = APIRouter(prefix="/v1")

    @router.post("/applications", response_model=ScoringResult)
    def score_application(application: CreditApplication, request: Request) -> ScoringResult:
        """Score one credit application, store it, and return the decision."""
        result = engine.score(application)
        repository: ApplicationStore = request.app.state.repository
        repository.save(result)
        return result

    @router.get("/applications/{application_id}", response_model=ScoringResult)
    def get_application(application_id: str, request: Request) -> ScoringResult:
        """Return a stored scoring result."""
        repository: ApplicationStore = request.app.state.repository
        result = repository.get(application_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Application not found")
        return result

    return router
