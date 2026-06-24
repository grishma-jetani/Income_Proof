# import jwt
# from fastapi import Depends, HTTPException, status
# from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# from app.core.config import settings

# bearer_scheme = HTTPBearer(auto_error=False)


# def get_current_user(
#     credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
# ) -> str:
#     """
#     FastAPI dependency.
#     Verifies the Supabase JWT from the Authorization header.
#     Returns the user's UUID as a string.
#     Raises 401 if the token is missing or invalid.
#     """
#     if credentials is None:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authorization header missing.",
#             headers={"WWW-Authenticate": "Bearer"},
#         )

#     token = credentials.credentials

#     if not settings.SUPABASE_JWT_SECRET:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="SUPABASE_JWT_SECRET is not configured on the server.",
#         )

#     try:
#         payload = jwt.decode(
#             token,
#             settings.SUPABASE_JWT_SECRET,
#             algorithms=["HS256"],
#             audience="authenticated",
#         )
#         user_id: str = payload.get("sub")
#         if not user_id:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Token payload missing 'sub' (user ID).",
#             )
#         return user_id

#     except jwt.ExpiredSignatureError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Session expired. Please sign in again.",
#         )
#     except jwt.InvalidTokenError as exc:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail=f"Invalid token: {exc}",
#         )

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)

# Fetch and cache the public keys from Supabase dynamically
jwks_client = None
if settings.SUPABASE_URL:
    jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    jwks_client = PyJWKClient(jwks_url)

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """
    FastAPI dependency.
    Verifies the Supabase JWT using Supabase's dynamic Public Keys (JWKS).
    Supports HS256, RS256, and ES256 algorithms natively.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not jwks_client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_URL is not configured on the server.",
        )

    token = credentials.credentials

    try:
        # Get the correct public key for this specific token
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["HS256", "RS256", "ES256"],
            audience="authenticated",
        )
        
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing 'sub' (user ID).",
            )
        return user_id

    except Exception as exc:
        print(f"JWT Verification Failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )