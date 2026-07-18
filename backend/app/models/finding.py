import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database.session import Base

class ReviewFinding(Base):
    __tablename__ = "review_findings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String, ForeignKey("analysis_reports.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    line_number = Column(Integer, nullable=True)
    severity = Column(String, nullable=False)          # "Critical", "High", "Medium", "Low", "Info"
    category = Column(String, nullable=False)          # "Security", "Performance", "Style", "Bug"
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    code_snippet = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    report = relationship("AnalysisReport", back_populates="findings")
