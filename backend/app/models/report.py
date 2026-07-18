import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database.session import Base

class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String, ForeignKey("code_submissions.id", ondelete="CASCADE"), nullable=False)
    summary = Column(Text, nullable=True)
    score = Column(Integer, default=100)             # Overall quality/security score 0-100
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    submission = relationship("CodeSubmission", back_populates="reports")
    findings = relationship("ReviewFinding", back_populates="report", cascade="all, delete-orphan", lazy="selectin")
    exports = relationship("ReportExport", back_populates="report", cascade="all, delete-orphan")
