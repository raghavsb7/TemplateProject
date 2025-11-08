"""
OAuth 2.0 Authentication module for Canvas, Microsoft, Google, and Handshake
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
import httpx
from fastapi import HTTPException, status

# OAuth Configuration
CANVAS_BASE_URL = os.getenv("CANVAS_BASE_URL", "https://canvas.instructure.com")
CANVAS_CLIENT_ID = os.getenv("CANVAS_CLIENT_ID", "")
CANVAS_CLIENT_SECRET = os.getenv("CANVAS_CLIENT_SECRET", "")

MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")
MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID", "common")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

HANDSHAKE_CLIENT_ID = os.getenv("HANDSHAKE_CLIENT_ID", "")
HANDSHAKE_CLIENT_SECRET = os.getenv("HANDSHAKE_CLIENT_SECRET", "")


class OAuthHandler:
    """Base OAuth handler"""
    
    @staticmethod
    def get_auth_url(source: str, redirect_uri: str, state: Optional[str] = None) -> str:
        """Get OAuth authorization URL for the given source"""
        if source == "canvas":
            return CanvasOAuth.get_auth_url(redirect_uri, state)
        elif source == "microsoft":
            return MicrosoftOAuth.get_auth_url(redirect_uri, state)
        elif source == "google":
            return GoogleOAuth.get_auth_url(redirect_uri, state)
        elif source == "handshake":
            return HandshakeOAuth.get_auth_url(redirect_uri, state)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source: {source}")
    
    @staticmethod
    async def exchange_code(source: str, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        if source == "canvas":
            return await CanvasOAuth.exchange_code(code, redirect_uri)
        elif source == "microsoft":
            return await MicrosoftOAuth.exchange_code(code, redirect_uri)
        elif source == "google":
            return await GoogleOAuth.exchange_code(code, redirect_uri)
        elif source == "handshake":
            return await HandshakeOAuth.exchange_code(code, redirect_uri)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source: {source}")
    
    @staticmethod
    async def refresh_token(source: str, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        if source == "canvas":
            return await CanvasOAuth.refresh_token(refresh_token)
        elif source == "microsoft":
            return await MicrosoftOAuth.refresh_token(refresh_token)
        elif source == "google":
            return await GoogleOAuth.refresh_token(refresh_token)
        elif source == "handshake":
            return await HandshakeOAuth.refresh_token(refresh_token)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported source: {source}")


class CanvasOAuth:
    """Canvas LMS OAuth 2.0"""
    
    @staticmethod
    def get_auth_url(redirect_uri: str, state: Optional[str] = None) -> str:
        params = {
            "client_id": CANVAS_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": redirect_uri,
        }
        if state:
            params["state"] = state
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{CANVAS_BASE_URL}/login/oauth2/auth?{query_string}"
    
    @staticmethod
    async def exchange_code(code: str, redirect_uri: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CANVAS_BASE_URL}/login/oauth2/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": CANVAS_CLIENT_ID,
                    "client_secret": CANVAS_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_uri,
                }
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Canvas OAuth error: {response.text}"
                )
            data = response.json()
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_at": expires_at,
                "token_type": data.get("token_type", "Bearer")
            }
    
    @staticmethod
    async def refresh_token(refresh_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CANVAS_BASE_URL}/login/oauth2/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": CANVAS_CLIENT_ID,
                    "client_secret": CANVAS_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                }
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Canvas token refresh error: {response.text}"
                )
            data = response.json()
            expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600))
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", refresh_token),
                "expires_at": expires_at,
                "token_type": data.get("token_type", "Bearer")
            }


class MicrosoftOAuth:
    """Microsoft Graph API OAuth 2.0"""
    
    @staticmethod
    def get_auth_url(redirect_uri: str, state: Optional[str] = None) -> str:
        scopes = "offline_access https://graph.microsoft.com/User.Read https://graph.microsoft.com/Calendars.Read https://graph.microsoft.com/Mail.Read"
        params = {
            "client_id": MICROSOFT_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "response_mode": "query",
            "scope": scopes,
        }
        if state:
            params["state"] = state
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/authorize?{query_string}"
    
    @staticmethod
    async def exchange_code(code: str, redirect_uri: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/token",
                data={
                    "client_id": MICROSOFT_CLIENT_ID,
                    "client_secret": MICROSOFT_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                }
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Microsoft OAuth error: {response.text}"
                )
            data = response.json()
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_at": expires_at,
                "token_type": data.get("token_type", "Bearer")
            }
    
    @staticmethod
    async def refresh_token(refresh_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://login.microsoftonline.com/{MICROSOFT_TENANT_ID}/oauth2/v2.0/token",
                data={
                    "client_id": MICROSOFT_CLIENT_ID,
                    "client_secret": MICROSOFT_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                }
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Microsoft token refresh error: {response.text}"
                )
            data = response.json()
            expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600))
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", refresh_token),
                "expires_at": expires_at,
                "token_type": data.get("token_type", "Bearer")
            }


class GoogleOAuth:
    """Google Calendar API OAuth 2.0"""
    
    @staticmethod
    def get_auth_url(redirect_uri: str, state: Optional[str] = None) -> str:
        scopes = "https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/userinfo.email"
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scopes,
            "access_type": "offline",
            "prompt": "consent",
        }
        if state:
            params["state"] = state
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
    
    @staticmethod
    async def exchange_code(code: str, redirect_uri: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                }
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Google OAuth error: {response.text}"
                )
            data = response.json()
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_at": expires_at,
                "token_type": data.get("token_type", "Bearer")
            }
    
    @staticmethod
    async def refresh_token(refresh_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                }
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Google token refresh error: {response.text}"
                )
            data = response.json()
            expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600))
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", refresh_token),
                "expires_at": expires_at,
                "token_type": data.get("token_type", "Bearer")
            }


class HandshakeOAuth:
    """Handshake OAuth 2.0 (placeholder - may need API access)"""
    
    @staticmethod
    def get_auth_url(redirect_uri: str, state: Optional[str] = None) -> str:
        # Handshake API documentation varies by institution
        # This is a placeholder implementation
        params = {
            "client_id": HANDSHAKE_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": redirect_uri,
        }
        if state:
            params["state"] = state
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        # Update with actual Handshake OAuth URL for your institution
        return f"https://api.joinhandshake.com/oauth/authorize?{query_string}"
    
    @staticmethod
    async def exchange_code(code: str, redirect_uri: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.joinhandshake.com/oauth/token",
                data={
                    "client_id": HANDSHAKE_CLIENT_ID,
                    "client_secret": HANDSHAKE_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                }
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Handshake OAuth error: {response.text}"
                )
            data = response.json()
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_at": expires_at,
                "token_type": data.get("token_type", "Bearer")
            }
    
    @staticmethod
    async def refresh_token(refresh_token: str) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.joinhandshake.com/oauth/token",
                data={
                    "client_id": HANDSHAKE_CLIENT_ID,
                    "client_secret": HANDSHAKE_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                }
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Handshake token refresh error: {response.text}"
                )
            data = response.json()
            expires_at = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600))
            return {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token", refresh_token),
                "expires_at": expires_at,
                "token_type": data.get("token_type", "Bearer")
            }

