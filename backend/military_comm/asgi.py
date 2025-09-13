"""
ASGI config for military_comm project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'military_comm.settings')

# Import Django ASGI application early to ensure the Django settings are loaded
django_asgi_app = get_asgi_application()

# Import routing after Django is initialized
from messaging.routing import websocket_urlpatterns as messaging_websocket_urlpatterns
from p2p_sync.routing import websocket_urlpatterns as p2p_sync_websocket_urlpatterns

# Combine all WebSocket URL patterns
websocket_urlpatterns = (
    messaging_websocket_urlpatterns +
    p2p_sync_websocket_urlpatterns
)

# ASGI application with WebSocket support for real-time military communications
application = ProtocolTypeRouter({
    # HTTP requests are handled by Django's ASGI application
    "http": django_asgi_app,
    
    # WebSocket requests for real-time P2P communication and messaging
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
