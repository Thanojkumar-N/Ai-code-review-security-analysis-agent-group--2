from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.user import (
    UserCreate, 
    UserLogin, 
    Token, 
    UserResponse, 
    TokenRefreshRequest, 
    ForgotPasswordRequest, 
    ResetPasswordRequest, 
    UserPasswordUpdate
)
from backend.app.services.auth_service import AuthService
from backend.app.middleware.auth import get_current_user
from backend.app.models.user import User
from backend.app.utils.security import get_password_hash, verify_password

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new developer user and seed default workspace project."""
    return AuthService.register_user(db, user_in)

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate email and password credentials, returning JWT access token."""
    return AuthService.authenticate_user(db, credentials)

@router.post("/refresh", response_model=Token)
def refresh(refresh_in: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Validate refresh token and rotate authentication keys."""
    return AuthService.refresh_token_session(db, refresh_in.refresh_token)

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Clear user session token in database, invalidating refresh credentials."""
    AuthService.logout_user(db, current_user)
    return {"message": "Successfully logged out"}

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
def forgot_password(forgot_in: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Initiate password recovery. Generates a mock debug token in response for sandbox testing."""
    return AuthService.process_forgot_password(db, forgot_in.email)

@router.post("/reset-password", status_code=status.HTTP_200_OK)
def reset_password(reset_in: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Verify recovery token code and assign new password credentials."""
    AuthService.process_reset_password(db, reset_in.email, reset_in.token, reset_in.new_password)
    return {"message": "Password successfully updated"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Fetch current authenticated user profile."""
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_profile(
    pass_update: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Securely update active user password validation keys."""
    if not verify_password(pass_update.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    current_user.hashed_password = get_password_hash(pass_update.new_password)
    current_user.refresh_token = None  # Force logout across other sessions
    db.commit()
    db.refresh(current_user)
    return current_user
