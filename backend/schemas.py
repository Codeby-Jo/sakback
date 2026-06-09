from pydantic import BaseModel

class UserCreate(BaseModel):
    name: str
    age: int
    city: str
    education: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    age: int
    city: str
    education: str
    email: str

    class Config:
        from_attributes = True
