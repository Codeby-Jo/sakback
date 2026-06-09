from fastapi import APIRouter
from nis.matcher import get_dummy_matches

router = APIRouter(tags=["matches"])

@router.get("/matches/{id}")
def matches(id: int):
    # Call the dummy NIS engine
    dummy_results = get_dummy_matches(id)
    return dummy_results
