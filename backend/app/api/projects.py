from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.core.database import get_db
from app.models.project import Project

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    description: str = ""

class ProjectOut(BaseModel):
    id: str
    name: str
    description: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=ProjectOut)
@router.post("/", response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=payload.name, description=payload.description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description or "",
        created_at=project.created_at.isoformat()
    )

@router.get("", response_model=List[ProjectOut])
@router.get("/", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return [
        ProjectOut(
            id=p.id,
            name=p.name,
            description=p.description or "",
            created_at=p.created_at.isoformat()
        ) for p in projects
    ]

@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(
        id=project.id,
        name=project.name,
        description=project.description or "",
        created_at=project.created_at.isoformat()
    )
