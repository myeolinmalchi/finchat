from pydantic import BaseModel


class UserIn(BaseModel):

    email: str
    nickname: str

    profile_image_url: str
