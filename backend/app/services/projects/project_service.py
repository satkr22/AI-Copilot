from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectStatus

class ProjectService:

    def __init__(self, db: Session):
        self.db = db

    def list_projects(self, user_id: str) -> list[Project]:

        return (
            self.db.query(Project)
            .filter(Project.user_id == user_id)
            .all()
        )
        
    def create_project(
        self, 
        user_id: str,
        data: ProjectCreate
    ) -> Project:
        project = Project(
            name=data.name,
            description=data.description,
            repository_id=data.repository_id,
            user_id=user_id,
            status=ProjectStatus.CREATED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        
        return project
    
    def fetch_project(
        self,
        user_id: str,
        project_id: str
    ) -> Project | None:

        return self.db.query(Project).filter(
                        Project.user_id == user_id,
                        Project.id == project_id).one_or_none()