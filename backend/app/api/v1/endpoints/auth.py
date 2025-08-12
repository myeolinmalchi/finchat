from urllib.parse import urlencode, urlparse, urlunparse
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from app.core.deps import inject

from dotenv import load_dotenv

from domains.auth.services import InvalidTokenError, TicketService, TokenService, KakaoOAuthService

from domains.auth.usecases import KakaoAuthUseCase
from domains.user.models import User
from domains.user.services import UserService

load_dotenv()

router = APIRouter(prefix="")


@router.get("/kakao/login")
def get_kakao_code(kakao_api: KakaoOAuthService = Depends(inject(KakaoOAuthService))):
    return RedirectResponse(kakao_api.auth_url)


@router.get("/kakao/callback")
async def kakao_redirection(code: str,
                            kakao_usecase: KakaoAuthUseCase = Depends(
                                inject(KakaoAuthUseCase))):

    kakao_result = await kakao_usecase.callback(code)

    query_string = urlencode({"ticket": kakao_result.raw_ticket})
    parsed_url = urlparse(kakao_result.redirect_url)
    redirect_url = urlunparse(parsed_url._replace(query=query_string))

    return RedirectResponse(url=redirect_url, status_code=302)


class ExchangeIn(BaseModel):
    ticket: str


class ExchangeOut(BaseModel):

    is_temporary: bool
    profile: User


@router.post("/exchange", response_model=ExchangeOut, status_code=200)
async def exchange_ticket(req: ExchangeIn,
                          res: Response,
                          token_service: TokenService = Depends(inject(TokenService)),
                          user_service: UserService = Depends(inject(UserService)),
                          ticket_service: TicketService = Depends(
                              inject(TicketService))):

    ticket = req.ticket
    if not ticket:
        raise HTTPException(400, "ticket required")

    user_id = await ticket_service.consume_ticket(ticket)
    _user = await user_service.get_user_by_id(user_id) if user_id else None

    if not user_id or not _user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                            content={"detail": "User not exists."})

    user, user_social = _user
    tokens = await token_service.issue_new_token_pair(user_id)

    res.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        #httponly=True,
        secure=False,
        #samesite="strict",
        samesite="lax",
        max_age=1800,
        path="/")

    res.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
        #httponly=True,
        secure=False,
        samesite="lax",
        max_age=1209600,
        path="/")

    return ExchangeOut(is_temporary=user_social.temp, profile=user)


@router.post("/token/refresh")
async def refresh_token(request: Request,
                        token_service: TokenService = Depends(inject(TokenService))):

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Refresh token not found in cookies")

    try:
        new_access_token = await token_service.refresh_access_token(refresh_token)
    except InvalidTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    response = JSONResponse(content={
        "status": "success",
        "message": "Access token refreshed"
    })

    response.set_cookie(key="access_token",
                        value=new_access_token,
                        httponly=True,
                        secure=True,
                        samesite="strict",
                        max_age=1800)

    return response


@router.post("/logout")
async def logout(request: Request,
                 response: Response,
                 token_service: TokenService = Depends(inject(TokenService))):

    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")

    if not access_token or not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = token_service.verify_and_decode_token(access_token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    await token_service.logout(user_id=user_id, refresh_token=refresh_token)

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
