from typing import Optional
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader

from app.config import settings
# from app.core.logging import LoggerMixin


# API Key authentication scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Bearer token authentication scheme (alternative)
security = HTTPBearer(auto_error=False)


class AuthService():
    """Authentication service for API key validation"""

    def __init__(self):
        self.valid_api_keys = set(settings.api_keys)
        if not self.valid_api_keys:
            print("No API keys configured - authentication will fail for all requests")

    def validate_api_key(self, api_key: str) -> bool:
        """Validate provided API key"""
        if not api_key:
            return False

        is_valid = api_key in self.valid_api_keys

        if not is_valid:
            print('Invalid API key attempted:', api_key[:8] + '...')

        return is_valid

    def authenticate_request(self, api_key: Optional[str] = None) -> bool:
        """Authenticate incoming request"""
        # Check if public access is enabled
        if settings.public_access_enabled:
            return True

        if not self.valid_api_keys:
            # If no API keys are configured, allow all requests (development mode)
            return True

        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="Missing API key. Provide X-API-Key header.",
                headers={"WWW-Authenticate": "ApiKey"}
            )

        if not self.validate_api_key(api_key):
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"}
            )

        return True


# Global auth service instance
auth_service = AuthService()


async def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """FastAPI dependency to extract and validate API key"""
    auth_service.authenticate_request(api_key)
    return api_key


async def get_bearer_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Optional[str]:
    """FastAPI dependency for bearer token authentication (alternative to API key)"""
    if credentials:
        auth_service.authenticate_request(credentials.credentials)
        return credentials.credentials
    else:
        auth_service.authenticate_request(None)
        return None
