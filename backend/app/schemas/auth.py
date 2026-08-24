"""
Pydantic schemas for authentication and user management.
"""
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

EMAIL_PATTERN = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"


class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    organization: str = Field(..., min_length=2, max_length=255)
    email: str = Field(..., pattern=EMAIL_PATTERN)
    password: str = Field(..., min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)
    password: str = Field(..., min_length=1)


class UserProfileResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    organization: str
    role: str
    is_verified: bool = False
    workspace_id: uuid.UUID
    workspace_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    message: str
    user: UserProfileResponse
    session_token: Optional[str] = None  # Returned as fallback for header auth if cookies disabled


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=16)
    new_password: str = Field(..., min_length=8, max_length=128)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)


class SessionInfoResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    expires_at: datetime
    is_current: bool = False

    class Config:
        from_attributes = True


class DeleteAccountRequest(BaseModel):
    password: str = Field(..., min_length=1)
    confirm_text: str = Field(..., description="Must match 'DELETE MY ACCOUNT'")

