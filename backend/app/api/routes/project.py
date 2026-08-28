from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.project import ProjectResponse, ProjectCreate
from app.services.projects.project_service import ProjectService

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)





@router.get("", response_model=list[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ProjectService(db)
    results = service.list_projects(current_user.id)

    return results


@router.post(
    "", 
    response_model=ProjectResponse,
    status_code=201
)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ProjectService(db)

    return service.create_project(current_user.id, data=project)
