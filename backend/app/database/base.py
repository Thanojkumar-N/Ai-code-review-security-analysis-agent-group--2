# Import all models to ensure they are registered with the declarative metadata before Alembic imports base.py
from backend.app.database.session import Base
from backend.app.models.user import User
from backend.app.models.project import Project
from backend.app.models.submission import CodeSubmission
from backend.app.models.report import AnalysisReport
from backend.app.models.finding import ReviewFinding
from backend.app.models.export import ReportExport
