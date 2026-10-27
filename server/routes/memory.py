"""
Experience memory API endpoints.
Provides past strategy inspection, success/failure advice, and record management.
"""

from fastapi import APIRouter, HTTPException, Query
from memory.experience_memory import ExperienceMemory

router = APIRouter(prefix="/api/memory", tags=["Experience Memory"])
memory = ExperienceMemory()


@router.get("")
async def list_experiences(limit: int = Query(default=50, ge=1, le=200)):
    """List all stored operational experiences, strategies, and failure patterns."""
    return memory.get_all_experiences(limit=limit)


@router.get("/advice")
async def get_advice(topic: str = Query(..., description="Domain or search topic")):
    """Query past experience for recommended strategies and pitfalls to avoid."""
    return memory.get_advice(topic)


@router.delete("/{entry_id}")
async def delete_experience(entry_id: int):
    """Delete a specific experience memory entry."""
    success = memory.delete_entry(entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="Experience entry not found")
    return {"status": "deleted", "entry_id": entry_id}


@router.delete("")
async def clear_all_memory():
    """Clear all stored experience memory."""
    memory.clear_memory()
    return {"status": "cleared", "message": "All experience records removed"}
