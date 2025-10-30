from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import GeneralDiary
from .. import schemas_fastapi

router = APIRouter(prefix="/general-diary", tags=["general-diary"])

@router.get("/", response_model=list[schemas_fastapi.GeneralDiaryOut])
def get_general_diary_entries(db: Session = Depends(get_db)):
    entries = db.query(GeneralDiary).all()
    return [schemas_fastapi.GeneralDiaryOut.model_validate(e) for e in entries]

@router.get("/{entry_id}", response_model=schemas_fastapi.GeneralDiaryOut)
def get_general_diary_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(GeneralDiary).filter(GeneralDiary.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return schemas_fastapi.GeneralDiaryOut.model_validate(entry)

@router.post("/", response_model=schemas_fastapi.GeneralDiaryOut)
def create_general_diary_entry(gd: schemas_fastapi.GeneralDiaryCreate, db: Session = Depends(get_db)):
    entry = GeneralDiary(**gd.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return schemas_fastapi.GeneralDiaryOut.model_validate(entry)

@router.put("/{entry_id}", response_model=schemas_fastapi.GeneralDiaryOut)
def update_general_diary_entry(entry_id: int, gd: schemas_fastapi.GeneralDiaryCreate, db: Session = Depends(get_db)):
    entry = db.query(GeneralDiary).filter(GeneralDiary.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    for name, value in gd.model_dump().items():
        setattr(entry, name, value)
    db.commit()
    db.refresh(entry)
    return schemas_fastapi.GeneralDiaryOut.model_validate(entry)

@router.delete("/{entry_id}")
def delete_general_diary_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(GeneralDiary).filter(GeneralDiary.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    return {"success": True}
