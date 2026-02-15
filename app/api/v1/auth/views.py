from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.database.unit_of_work import UnitOfWorkConnection, get_uow
from app.exceptions.exceptions import NotFoundError
from app.schemas.auth import Token, UserLogin
from app.services.auth.authentication import AuthService
from app.services.auth.google_oauth import GoogleOAuthService, get_google_oauth_service
from app.core.logger import logger

router = APIRouter(prefix="/auth")


@router.post("/token", response_model=Token)
async def login(form: UserLogin, uow: UnitOfWorkConnection = Depends(get_uow)):
    logger.info(f"[INFO] Tentando autenticar usuário: {form.email}")
    service = AuthService()
    user = await service.authenticate(form.email, form.password, uow)
    logger.info(
        f"[INFO] Usuário autenticado: {user.email if user else 'Usuário não encontrado'}"
    )
    if not user:
        raise NotFoundError
    return await service.issue_token(user.email, uow)


@router.get("/google/login")
async def google_login(
    google_service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    """Redireciona para a página de login do Google."""
    auth_data = await google_service.get_authorization_url(
        redirect_uri=google_service.settings.GOOGLE_REDIRECT_URI
    )
    return auth_data


@router.get("/google/callback")
async def google_callback(
    request: Request,
    uow: UnitOfWorkConnection = Depends(get_uow),
    google_service: GoogleOAuthService = Depends(get_google_oauth_service),
):
    """Callback do Google OAuth - processa o código e cria/atualiza usuário."""
    # Obtém informações do usuário do Google
    user_info = await google_service.get_user_info(request)

    if not user_info:
        raise HTTPException(
            status_code=400, detail="Falha ao obter informações do Google"
        )

    # Autentica/cria usuário
    auth_service = AuthService()
    user = await auth_service.authenticate_google_user(
        google_id=user_info["google_id"],
        email=user_info["email"],
        name=user_info["name"],
        uow=uow,
    )

    # Gera token JWT
    token = await auth_service.issue_token(user.email, uow)

    # Redireciona para o frontend com o token
    frontend_url = f"http://localhost:8080/?token={token.access_token}"
    return RedirectResponse(url=frontend_url)
