import os
import uuid
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException, status
from backend.app.models.submission import CodeSubmission
from backend.app.models.project import Project
from backend.app.config.config import settings
from backend.app.utils.syntax_validator import validate_code_syntax

class SubmissionService:
    @staticmethod
    def get_user_projects(db: Session, user_id: str):
        """Retrieve all projects belonging to a user."""
        return db.query(Project).filter(Project.user_id == user_id).all()

    @staticmethod
    def create_project(db: Session, name: str, description: str, user_id: str) -> Project:
        """Create a new project container for code submissions."""
        project = Project(
            name=name,
            description=description,
            user_id=user_id
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def create_paste_submission(db: Session, project_id: str, raw_code: str, user_id: str, language: str = "python") -> CodeSubmission:
        """Create a database submission record for raw pasted text, after validating syntax."""
        project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target project not found"
            )

        # Run syntax validation based on language hint
        lang_filename = "main.py" if language.lower() == "python" else "Main.java"
        try:
            validate_code_syntax(lang_filename, raw_code)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        submission = CodeSubmission(
            project_id=project_id,
            user_id=user_id,
            submission_type="paste",
            raw_code=raw_code,
            status="pending"
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission

    @staticmethod
    async def create_file_submission(
        db: Session, 
        project_id: str, 
        file: UploadFile, 
        user_id: str
    ) -> CodeSubmission:
        """Process, validate size/extensions, save, and check code syntax before committing to DB."""
        project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Target project not found"
            )

        # 1. Enforce file size check using tell-and-seek
        try:
            file.file.seek(0, 2)
            file_size = file.file.tell()
            file.file.seek(0)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to inspect upload stream: {str(e)}"
            )

        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds the {settings.MAX_UPLOAD_SIZE / 1024 / 1024:.1f}MB maximum limit"
            )

        # 2. Restrict extensions
        file_ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        allowed = settings.ALLOWED_EXTENSIONS.split(",")
        if file_ext not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: '.{file_ext}'. Allowed formats: {', '.join(allowed)}"
            )

        # Create uploads folder if missing
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

        # Save file with unique ID prefix to prevent filename collision
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        save_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        try:
            with open(save_path, "wb") as f:
                # Read chunks to avoid overwhelming RAM memory
                while chunk := await file.read(65536):
                    f.write(chunk)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to write file storage: {str(e)}"
            )

        # 3. Read saved file and execute syntax validation
        try:
            with open(save_path, "r", encoding="utf-8", errors="ignore") as f:
                file_content = f.read()
            validate_code_syntax(file.filename, file_content)
        except ValueError as e:
            # Delete invalid file to clean disk storage
            if os.path.exists(save_path):
                os.remove(save_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            if os.path.exists(save_path):
                os.remove(save_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal parser failure: {str(e)}"
            )

        submission = CodeSubmission(
            project_id=project_id,
            user_id=user_id,
            submission_type="upload",
            file_path=save_path,
            status="pending"
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
        return submission
