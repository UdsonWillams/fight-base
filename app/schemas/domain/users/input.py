from pydantic import BaseModel, EmailStr, field_validator


class CreateUser(BaseModel):
    """Schema para criação de usuário (registro público)."""

    email: EmailStr
    password: str
    name: str
    username: str


class AdminCreateUser(BaseModel):
    """Schema para criação de usuário pelo admin (permite definir role)."""

    email: EmailStr
    password: str
    name: str
    username: str
    role: str = "user"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("admin", "user"):
            raise ValueError('role must be "admin" or "user"')
        return v


class UpdateUser(BaseModel):
    """Schema para atualização de usuário."""

    name: str | None = None
    password: str | None = None
    email: EmailStr | None = None
