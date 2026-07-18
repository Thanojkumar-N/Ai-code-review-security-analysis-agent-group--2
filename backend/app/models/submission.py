import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database.session import Base

class CodeSubmission(Base):
    __tablename__ = "code_submissions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    submission_type = Column(String, nullable=False)  # "upload" or "paste"
    file_path = Column(String, nullable=True)          # Saved path for zip/file uploads
    raw_code = Column(Text, nullable=True)            # Code pasted directly
    status = Column(String, default="pending")        # "pending", "running", "completed", "failed"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="submissions")
    project = relationship("Project", back_populates="submissions")
    reports = relationship("AnalysisReport", back_populates="submission", cascade="all, delete-orphan")
