import os
import uuid
import logging
from celery import Task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.statement import Statement
from app.services.pipeline import run_pipeline

logger = logging.getLogger(__name__)

class ProcessStatementTask(Task):
    """Custom task with automatic retry on failure"""
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 60
    retry_jitter = True

@celery_app.task(base=ProcessStatementTask, bind=True)
def process_statement(self, statement_id: str, filepath: str, user_id: str):
    logger.info(f"Starting task for statement {statement_id}")
    
    # --- FIX #1: Set status to "processing" instantly ---
    try:
        db = SessionLocal()
        stmt = db.get(Statement, uuid.UUID(statement_id))
        if stmt:
            stmt.status = "processing"
            db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Could not update status to processing: {e}")

    try:
        stmt_uuid = uuid.UUID(statement_id)
        user_uuid = user_id 
        
        result = run_pipeline(stmt_uuid, filepath, user_uuid)
        
        logger.info(f"Task completed for statement {statement_id}")
        return {"status": "success", "statement_id": statement_id}
        
    except Exception as e:
        logger.error(f"Task failed for statement {statement_id}: {str(e)}")
        try:
            db = SessionLocal()
            stmt = db.get(Statement, uuid.UUID(statement_id))
            if stmt:
                stmt.status = "failed"
                db.commit()
            db.close()
        except Exception as db_err:
            logger.error(f"Could not update statement status: {db_err}")
        raise
        
    finally:
        # --- FIX #2: Clean up raw file to save disk space ---
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Cleaned up raw file: {filepath}")