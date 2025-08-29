from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from urllib.parse import parse_qs
from asgiref.sync import sync_to_async
import logging

# Fetch user from token using sync_to_async
@sync_to_async
def get_user_from_token(token_key):
    try:
        token = Token.objects.get(key=token_key)  # Query to get the user by token
        logging.info(f"Token found for user: {token.user}")
        return token.user
    except Token.DoesNotExist:
        logging.info(f"Token {token_key} not found, returning AnonymousUser")
        return AnonymousUser()

class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        # Close old database connections to prevent stale connections
        close_old_connections()

        # Extract token from query string
        token_key = parse_qs(scope['query_string'].decode()).get('token', None)

        # Fetch user if token is present, otherwise use AnonymousUser
        if token_key:
            logging.info(f"Token provided: {token_key[0]}")
            scope['user'] = await get_user_from_token(token_key[0])
        else:
            logging.info("No token provided, assigning AnonymousUser")
            scope['user'] = AnonymousUser()

        # Continue processing with the authenticated user
        return await super().__call__(scope, receive, send)

# Create the TokenAuthMiddlewareStack
TokenAuthMiddlewareStack = lambda inner: TokenAuthMiddleware(AuthMiddlewareStack(inner))
