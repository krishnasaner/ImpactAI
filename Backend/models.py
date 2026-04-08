https://github.com/krishnasaner/ImpactAI.gitfrom datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class UserInDB(BaseModel):
    id: str
    email: EmailStr
    hashed_password: str
    role: str
    name: Optional[str]
    created_at: datetime
