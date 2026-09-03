from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectRepositoryAttach,
    ProjectResponse,
    ProjectCreate
)
from app.schemas.repository import GithubRepositoryCreate, RepositoryResponse
from app.services.projects.project_service import ProjectService
from app.services.repositories.repository_service import RepositoryService

router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)





@router.get(
    "", 
    response_model=list[ProjectResponse], 
    status_code=200
)
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


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=200
)
def get_project_by_id(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ProjectService(db=db)
    
    result = service.fetch_project(current_user.id, project_id=project_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project doesn't exist."
        )
    return result


@router.get(
    "/{project_id}/repository",
    response_model=RepositoryResponse,
    status_code=200
)
def get_project_repository(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = RepositoryService(db=db)

    return service.get_project_repository(
        user_id=current_user.id,
        project_id=project_id
    )


@router.put(
    "/{project_id}/repository",
    response_model=RepositoryResponse,
    status_code=200
)
def attach_existing_repository(
    project_id: str,
    payload: ProjectRepositoryAttach,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = RepositoryService(db=db)

    return service.attach_repository(
        user_id=current_user.id,
        project_id=project_id,
        repository_id=payload.repository_id
    )


@router.post(
    "/{project_id}/repository/github",
    response_model=RepositoryResponse,
    status_code=201
)
def create_github_repository_for_project(
    project_id: str,
    payload: GithubRepositoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = RepositoryService(db=db)

    try:
        result = service.create_github_repository_for_project(
            user_id=current_user.id,
            project_id=project_id,
            data=payload
        )
        return result
    
    except Exception as e:
        print("Caught:", e)
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Cloning failed",
        )


@router.post(
    "/{project_id}/repository/zip",
    response_model=RepositoryResponse,
    status_code=201
)
def upload_zip_repository_for_project(
    project_id: str,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):  
    service = RepositoryService(db=db)
    try:     
        repo =  service.create_zip_repository_for_project(
            user_id=current_user.id,
            project_id=project_id,
            file=file
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="ZIP extraction failed or unsupported zip."
        )
    return repo


@router.delete(
    "/{project_id}/repository",
    response_model=ProjectResponse,
    status_code=200
)
def detach_repository_from_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = RepositoryService(db=db)

    return service.detach_repository_from_project(
        user_id=current_user.id,
        project_id=project_id
    )


@router.delete(
    "/{project_id}",
    status_code=204
)
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project_service = ProjectService(db=db)
    repo_service = RepositoryService(db=db)

    old_repository_id = project_service.delete_project(
        user_id=current_user.id,
        project_id=project_id
    )

    if old_repository_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # If the project had a repository, clean it up if orphaned
    if old_repository_id != "no_repo":
        repo_service.cleanup_repository_if_orphan(
            user_id=current_user.id,
            repository_id=old_repository_id
        )
        
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
