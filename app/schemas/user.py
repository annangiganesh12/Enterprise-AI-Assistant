
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):

    username: str = Field(
        min_length=3,
        max_length=50
    )

    email: EmailStr
    password: str = Field(min_length=8)
    role: str = Field(default="employee", description="User role (e.g., admin, employee)")

class UserLogin(BaseModel):

    email: EmailStr
    password: str

class UserResponse(BaseModel):

    id: int
    username: str
    email: EmailStr
    role: str

model_config = {
    "from_attributes": True
}
 