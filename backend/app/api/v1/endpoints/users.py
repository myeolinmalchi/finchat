from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.deps import inject
from app.schemas.user import UserIn
from domains.auth.services import InvalidTokenError, TokenService
from domains.user.models import User
from domains.user.repositories import UserRepository
from domains.user.services import AlreadyRegistered, SocialAccountNotFound, UserMemoryService, UserService

router = APIRouter(prefix="")


async def get_current_user(req: Request,
                           token_service: TokenService = Depends(inject(TokenService)),
                           user_repo: UserRepository = Depends(inject(UserRepository))):

    access_token = req.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = token_service.verify_and_decode_token(access_token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        user = await user_repo.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired or is invalid",
        )


@router.get("/me", status_code=200)
async def get_user_info(user: Optional[User] = Depends(get_current_user)):
    return user


@router.get("/me/memories", status_code=200)
async def get_memories(req: Request,
                       memory_service: UserMemoryService = Depends(
                           inject(UserMemoryService))):
    memories = await memory_service.list_memories(user_id=req.state.user_id)
    return {
        "offset":
            0,
        "size":
            len(memories),
        "items": [{
            "memory_id": m.id,
            "content": m.content,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        } for m in memories]
    }


@router.delete("/me/memories/{memory_id}")
async def delete_memory(memory_id: str,
                        memory_service: UserMemoryService = Depends(
                            inject(UserMemoryService))):
    print(memory_id)
    await memory_service.remove_memory(memory_id=memory_id)


@router.post("/signup")
async def user_signup(user_in: UserIn,
                      user: Optional[User] = Depends(get_current_user),
                      user_service: UserService = Depends(inject(UserService))):

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자 정보가 없습니다.",
        )

    try:
        await user_service.signup(user.id, user_in)
    except SocialAccountNotFound:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자 정보가 없습니다.",
        )
    except AlreadyRegistered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 가입된 사용자입니다.",
        )

    return Response(status_code=status.HTTP_201_CREATED)
