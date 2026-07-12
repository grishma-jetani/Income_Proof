import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.upload import router as upload_router
from app.api.statements import router as statements_router
from app.api.dashboard import router as dashboard_router
from app.api.report import router as report_router
from app.api.task_status import router as task_status_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="IncomeProof API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(statements_router)
app.include_router(dashboard_router)
app.include_router(report_router)
app.include_router(task_status_router)

@app.get("/health")
def health():
    return {"healthy": True}
