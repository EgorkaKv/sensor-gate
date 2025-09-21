from fastapi import Depends
from typing import Optional

from app.services.auth import get_api_key
from app.services.pubsub import pubsub_service, PubSubService


async def get_pubsub_service() -> PubSubService:
    """FastAPI dependency to get PubSub service instance"""
    return pubsub_service


async def get_authenticated_request(api_key: Optional[str] = Depends(get_api_key)) -> Optional[str]:
    """FastAPI dependency for authenticated requests"""
    return api_key
