from __future__ import annotations

import jwt
from jwt import PyJWKClient
from typing import Dict
from .config import settings

# DEPRECATED: Legacy token store for backward compatibility
tokens_db: Dict[str, str] = {}


def verify_supabase_token(token: str) -> dict:
    """Verify a Supabase JWT token and return the payload.
    
    This function supports both:
    1. New ECC P-256 keys (ES256) via JWKS endpoint
    2. Legacy HS256 shared secret for backward compatibility
    
    Args:
        token: The JWT token from Supabase
        
    Returns:
        dict: Token payload containing user info (sub, email, user_metadata, etc.)
        
    Raises:
        ValueError: If token is invalid or expired
    """
    # Try ES256 via JWKS first (for new ECC keys)
    if settings.SUPABASE_JWKS_URL:
        try:
            jwk_client = PyJWKClient(settings.SUPABASE_JWKS_URL)
            signing_key = jwk_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                options={"verify_aud": False},  # Supabase uses aud='authenticated'
            )
            print(f"Token verified via JWKS (ES256)")
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except Exception as e:
            # If JWKS verification fails, try HS256 fallback
            print(f"⚠️  JWKS verification failed: {e}")
            pass
    
    # Fallback to HS256 (legacy shared secret)
    if settings.SUPABASE_JWT_SECRET:
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {str(e)}")
        except Exception as e:
            print(f"⚠️  HS256 verification failed: {e}")
    
    raise ValueError("Unable to verify token: No valid verification method configured")


def verify_access_token(token: str) -> dict:
    """DEPRECATED: Use verify_supabase_token instead.
    
    This function attempts to verify as a Supabase token first,
    then falls back to the legacy token store for backward compatibility.
    """
    # Try Supabase JWT first
    try:
        return verify_supabase_token(token)
    except ValueError:
        pass
    
    # Fallback to legacy token store
    username = tokens_db.get(token)
    if not username:
        raise ValueError("Invalid token")
    return {"sub": username, "email": username}
