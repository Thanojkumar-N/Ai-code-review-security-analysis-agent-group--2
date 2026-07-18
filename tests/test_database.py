import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from backend.app.database.base import Base
from backend.app.models.user import User
from backend.app.models.project import Project
from backend.app.models.submission import CodeSubmission
from backend.app.models.report import AnalysisReport
from backend.app.models.finding import ReviewFinding

# Local SQLite configuration for isolated database testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Create all schema tables in the temporary database file."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Remove SQLite file safely
    if os.path.exists("./test_database.db"):
        try:
            os.remove("./test_database.db")
        except Exception:
            pass

@pytest.fixture
def db():
    """Provide a database session fixture for transaction rollbacks."""
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()

def test_user_email_unique_constraint(db):
    """Verify that creating two users with the same email raises an IntegrityError."""
    user1 = User(email="dup@test.com", hashed_password="hash123", role="Developer")
    db.add(user1)
    db.commit()

    user2 = User(email="dup@test.com", hashed_password="hash456", role="Developer")
    db.add(user2)
    
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()

def test_project_cascading_delete(db):
    """Verify that deleting a Project cascadingly deletes associated Submissions, Reports, and Findings."""
    # 1. Create User, Project, Submission, Report, Finding
    user = User(email="cascade@test.com", hashed_password="hash", role="Developer")
    db.add(user)
    db.commit()

    project = Project(name="Delete Cascade Project", description="Verify cascades", user_id=user.id)
    db.add(project)
    db.commit()

    submission = CodeSubmission(
        project_id=project.id,
        user_id=user.id,
        submission_type="paste",
        raw_code="print('test')",
        status="completed"
    )
    db.add(submission)
    db.commit()

    report = AnalysisReport(
        submission_id=submission.id,
        summary="Test report summary",
        score=95
    )
    db.add(report)
    db.commit()

    finding = ReviewFinding(
        report_id=report.id,
        file_path="main.py",
        line_number=10,
        severity="Low",
        category="Code Quality",
        title="Smell",
        description="smell details",
        recommendation="rec"
    )
    db.add(finding)
    db.commit()

    # Verify entities exist in database
    assert db.query(Project).filter(Project.id == project.id).count() == 1
    assert db.query(CodeSubmission).filter(CodeSubmission.id == submission.id).count() == 1
    assert db.query(AnalysisReport).filter(AnalysisReport.id == report.id).count() == 1
    assert db.query(ReviewFinding).filter(ReviewFinding.id == finding.id).count() == 1

    # 2. Trigger Delete Cascade
    db.delete(project)
    db.commit()

    # 3. Assert all children are deleted cascadingly
    assert db.query(Project).filter(Project.id == project.id).count() == 0
    assert db.query(CodeSubmission).filter(CodeSubmission.id == submission.id).count() == 0
    assert db.query(AnalysisReport).filter(AnalysisReport.id == report.id).count() == 0
    assert db.query(ReviewFinding).filter(ReviewFinding.id == finding.id).count() == 0
