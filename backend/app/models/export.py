import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database.session import Base

class ReportExport(Base):
    __tablename__ = "report_exports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String, ForeignKey("analysis_reports.id", ondelete="CASCADE"), nullable=False)
    export_type = Column(String, nullable=False)       # "PDF", "JSON", "CSV"
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    report = relationship("AnalysisReport", back_populates="exports")
