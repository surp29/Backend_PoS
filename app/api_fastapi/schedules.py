from fastapi import APIRouter

router = APIRouter(prefix="/schedules", tags=["schedules"]) 

@router.get("/")
def list_schedules():
    # Minimal placeholder to avoid 404; FE currently only loads list
    return []


