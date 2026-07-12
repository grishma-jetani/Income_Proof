import os
import uuid
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.statement import Statement
from app.schemas.statement import StatementUploadResponse
from app.tasks.process_statement import process_statement

router = APIRouter(prefix="/api", tags=["upload"])

ALLOWED_EXTENSIONS = {".pdf", ".csv"}

@router.post("/upload", response_model=list[StatementUploadResponse])
async def upload_statements(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
    files: list[UploadFile] = File(...),
    source_labels: str = Form(default=""),
):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    labels = [l.strip() for l in source_labels.split(",")]
    responses = []
    
    for i, upload_file in enumerate(files):
        ext = os.path.splitext(upload_file.filename)[1].lower()
        
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{ext}' for '{upload_file.filename}'. Only PDF and CSV accepted.",
            )
        
        file_id = uuid.uuid4()
        saved_filename = f"{file_id}{ext}"
        saved_path = os.path.join(settings.UPLOAD_DIR, saved_filename)
        
        contents = await upload_file.read()
        with open(saved_path, "wb") as f:
            f.write(contents)
        
        label = labels[i] if i < len(labels) else "Unknown"
        
        stmt = Statement(
            id=file_id,
            user_id=uuid.UUID(current_user),
            filename=upload_file.filename,
            source_label=label,
            file_path=saved_path,
            status="pending",
        )
        db.add(stmt)
        db.commit()
        db.refresh(stmt)
        
        task = process_statement.delay(str(stmt.id), saved_path, current_user)
        
        responses.append(
            StatementUploadResponse(
                statement_id=stmt.id,
                filename=upload_file.filename,
                status="pending",
            )
        )
    
    return responses
