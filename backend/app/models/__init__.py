# Importing every model here ensures Alembic's autogenerate sees all tables
from app.models.user import User
from app.models.statement import Statement
from app.models.transaction import Transaction
from app.models.stability_metric import StabilityMetric