from fastapi import APIRouter
from app.core.celery_app import celery_app

router = APIRouter(prefix="/api", tags=["tasks"])

@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    result = celery_app.AsyncResult(task_id)
    
    if result.pending:
        return {"status": "pending", "task_id": task_id, "progress": 0}
    elif result.failed():
        return {"status": "failed", "task_id": task_id, "error": str(result.info)}
    elif result.successful():
        return {"status": "completed", "task_id": task_id, "result": result.result}
    else:
        return {"status": result.state, "task_id": task_id, "info": str(result.info) if result.info else None}