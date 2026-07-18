from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models.user import User
from backend.app.models.project import Project
from backend.app.schemas.user import UserCreate, UserLogin, Token, UserResponse
from backend.app.utils.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token, 
    decode_access_token
)
from jose import jwt, JWTError
from backend.app.config.config import settings

class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        """Register a new user, check for email duplicate, hash password, and seed default project."""
        existing_user = db.query(User).filter(User.email == user_in.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password and create record
        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            role=user_in.role or "Developer",
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Seed initial workspace project for the developer
        default_project = Project(
            name="My Workspace Project",
            description="Default repository for reviewing uploaded and pasted code.",
            user_id=db_user.id
        )
        db.add(default_project)
        db.commit()

        return db_user

    @staticmethod
    def authenticate_user(db: Session, credentials: UserLogin) -> Token:
        """Authenticate user credentials, save and return rotated access and refresh tokens."""
        user = db.query(User).filter(User.email == credentials.email).first()
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user account"
            )

        # Generate JWT access and refresh tokens
        access_token = create_access_token(
            subject=user.email,
            role=user.role,
            user_id=user.id
        )
        refresh_token = create_refresh_token(
            subject=user.email,
            role=user.role,
            user_id=user.id
        )

        # Save refresh token in database (hashed or direct string, direct string matches standard tracking)
        user.refresh_token = refresh_token
        db.commit()
        db.refresh(user)
        
        user_res = UserResponse.model_validate(user)
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_res
        )

    @staticmethod
    def refresh_token_session(db: Session, refresh_token: str) -> Token:
        """Validate the refresh token, rotate tokens, and update database."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        payload = decode_access_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise credentials_exception
            
        user_id: str = payload.get("user_id")
        email: str = payload.get("sub")
        if user_id is None or email is None:
            raise credentials_exception
            
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active or user.refresh_token != refresh_token:
            # Token reuse or invalid token
            raise credentials_exception

        # Rotate tokens
        new_access_token = create_access_token(
            subject=user.email,
            role=user.role,
            user_id=user.id
        )
        new_refresh_token = create_refresh_token(
            subject=user.email,
            role=user.role,
            user_id=user.id
        )

        # Save rotated refresh token in database
        user.refresh_token = new_refresh_token
        db.commit()
        db.refresh(user)

        user_res = UserResponse.model_validate(user)
        return Token(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            user=user_res
        )

    @staticmethod
    def logout_user(db: Session, user: User) -> None:
        """Clear user's refresh token record, invalidating active sessions."""
        user.refresh_token = None
        db.commit()

    @staticmethod
    def process_forgot_password(db: Session, email: str) -> dict:
        """Process forgot password request. Logs recovery code in console for mock use."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Avoid exposing registered emails (security best practice)
            return {"message": "If the email is registered, recovery instructions have been sent."}
            
        # Return a mock token for test verification purposes
        mock_token = f"recovery_code_{user.id[:8]}"
        import logging
        logging.info(f"PASSWORD RECOVERY TRACE FOR {email}: Token is {mock_token}")
        return {
            "message": "If the email is registered, recovery instructions have been sent.",
            "debug_token": mock_token  # Expose token for simpler testing sandbox
        }

    @staticmethod
    def process_reset_password(db: Session, email: str, token: str, new_password: str) -> None:
        """Verify the mock token and update the user's password."""
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        expected_token = f"recovery_code_{user.id[:8]}"
        if token != expected_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid recovery token"
            )

        # Update user's password and reset active sessions
        user.hashed_password = get_password_hash(new_password)
        user.refresh_token = None
        db.commit()

