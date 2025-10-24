from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import GeneralDiary
from .. import crud, schemas_fastapi

router = APIRouter(prefix="/general-diary", tags=["general-diary"])


@router.get("/{entry_id}")
def get_general_diary_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = crud.get_general_diary_entry(db, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"success": True, "data": entry}


@router.get("/")
def get_general_diary(db: Session = Depends(get_db)):
    entries = crud.get_general_diary(db)
    return {"success": True, "data": entries}


@router.post("/")
def create_general_diary_entry(gd: schemas_fastapi.GeneralDiaryCreate, db: Session = Depends(get_db)):
    try:
        entry = crud.create_general_diary(db, gd)
        return {"success": True, "id": entry.id, "data": entry}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{entry_id}")
def update_general_diary_entry(entry_id: int, gd: schemas_fastapi.GeneralDiaryCreate, db: Session = Depends(get_db)):
    try:
        entry = crud.update_general_diary(db, entry_id, gd)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        return {"success": True, "data": entry}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{entry_id}")
def delete_general_diary_entry(entry_id: int, db: Session = Depends(get_db)):
    try:
        entry = crud.delete_general_diary(db, entry_id)
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        return {"success": True, "message": "Entry deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
