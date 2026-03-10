from typing import Dict, Optional
from authlib.integrations.starlette_client import OAuth
from app.core.settings import get_settings


class GoogleOAuthService:
    def __init__(self):
        self.settings = get_settings()
        self.oauth = OAuth()
        self.oauth.register(
            name="google",
            client_id=self.settings.GOOGLE_CLIENT_ID,
            client_secret=self.settings.GOOGLE_CLIENT_SECRET,
            server_metadata_url=self.settings.GOOGLE_DISCOVERY_URL,
            client_kwargs={"scope": "openid email profile"},
        )

    async def get_authorization_url(self, redirect_uri: str) -> Dict[str, str]:
        """Gera URL de autorização do Google."""
        google = self.oauth.create_client("google")
        redirect_uri = redirect_uri or self.settings.GOOGLE_REDIRECT_URI
        return await google.authorize_redirect(None, redirect_uri)

    async def get_user_info(self, request) -> Optional[Dict]:
        """Obtém informações do usuário a partir do callback (request)."""
        google = self.oauth.create_client("google")
        token = await google.authorize_access_token(request)

        # Extrai informações do token
        user_info = token.get("userinfo")
        if user_info:
            return {
                "google_id": user_info.get("sub"),
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
            }
        return None


def get_google_oauth_service() -> GoogleOAuthService:
    return GoogleOAuthService()
