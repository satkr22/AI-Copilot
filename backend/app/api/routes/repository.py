from fastapi.routing import APIRouter

router = APIRouter(
    prefix="/repositories",
    tags=["Repositories"]
)
