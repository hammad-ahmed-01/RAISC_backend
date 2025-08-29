import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RAISC_backend.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import SessionMiddlewareStack
from _chat.middleware.token_auth_middleware import TokenAuthMiddlewareStack  # Import your custom middleware
import _chat.routing  # Your WebSocket routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'RAISC_backend.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": SessionMiddlewareStack(  # Ensure sessions are handled for WebSockets
        TokenAuthMiddlewareStack(  # Use custom TokenAuthMiddlewareStack
            URLRouter(
                _chat.routing.websocket_urlpatterns
            )
        )
    ),
})