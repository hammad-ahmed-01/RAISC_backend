from django.urls import re_path
from .consumers import ChatConsumer  # Ensure ChatConsumer is correctly defined

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<group_id>\w+)/$', ChatConsumer.as_asgi()),
]
