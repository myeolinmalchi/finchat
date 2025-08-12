from fastapi import APIRouter
from app.api.v1.endpoints import chat, auth, users

router = APIRouter()

router.include_router(chat.router, prefix="/chats", tags=["chats"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
