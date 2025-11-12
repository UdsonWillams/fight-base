from pydantic import BaseModel, EmailStr


class CreateUser(BaseModel):
    """Schema para criação de usuário."""

    email: EmailStr
    password: str
    name: str


class UpdateUser(BaseModel):
    """Schema para atualização de usuário."""

    name: str | None = None
    password: str | None = None
    email: EmailStr | None = None
