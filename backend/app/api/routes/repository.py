from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db

from app.models.user import User

from app.schemas.repository import RepositoryResponse
from app.schemas.indexing import IndexingJobResponse

from app.services.repositories.repository_service import RepositoryService

router = APIRouter(
    prefix="/repositories",
    tags=["Repositories"]
)


@router.get(
    "",
    response_model=list[RepositoryResponse],
    status_code=200
)
def list_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = RepositoryService(db)

    return service.list_repositories(current_user.id)


@router.get(
    "/{repository_id}",
    response_model=RepositoryResponse,
    status_code=200
)
def get_repository(
    repository_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = RepositoryService(db)
    repository = service.get_repository(
        user_id=current_user.id,
        repository_id=repository_id
    )

    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )

    return repository



@router.post(
    "/{repository_id}/index",
    response_model=IndexingJobResponse,
    status_code=status.HTTP_200_OK
)
def index_repository(
    repository_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = RepositoryService(db)
    return service.index_repository(
            current_user.id,
            repository_id
    )
    