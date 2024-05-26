"""
ASGI config for websocket_chats_notifications project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve(strict=True).parent.parent
sys.path.append(str(ROOT_DIR / "websockets_chats_notifications"))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'websocket_chats_notifications.settings')

django_asgi_app = get_asgi_application()

from django.urls import re_path
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from chats_notifications import consumers

websocket_urlpatterns = [
    re_path(
        r"ws/direct-chat/",
        consumers.DirectChatConsumer.as_asgi(),
    ),
    # re_path(
    #     r"ws/chats-list/",
    #     consumers.ApplicationsChatsConversationsListConsumer.as_asgi(),
    # ),
    re_path(
        r"ws/notifications/",
        consumers.NotificationsConsumer.as_asgi(),
    ),
    # re_path(r"ws/group-chat/", consumers.ApplicationsChatsGroupConsumer.as_asgi()),
]

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": AuthMiddlewareStack(
            AllowedHostsOriginValidator(URLRouter(websocket_urlpatterns))
        ),
    }
)
