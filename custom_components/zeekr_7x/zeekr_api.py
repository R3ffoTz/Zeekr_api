"""Zeekr API wrapper for Home Assistant."""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

_LOGGER = logging.getLogger(__name__)

STORAGE_VERSION = 1
STORAGE_KEY = "zeekr_tokens"


class ZeekrAPI:
    """Zeekr API client."""
    
    def __init__(
        self,
        hass: HomeAssistant,
        email: str | None = None,
        password: str | None = None,
        access_token: str | None = None,
        refresh_token: str | None = None,
        vin: str | None = None,
    ) -> None:
        """Initialize the API client."""
        self.hass = hass
        self.email = email
        self.password = password
        self.vin = vin
        
        self.base_url = "https://eu-snc-tsp-api-gw.zeekrlife.com"
        
        # Token storage
        self.access_token: str | None = access_token
        self.refresh_token: str | None = refresh_token
        self.token_expires_at: float = 0
        self.refresh_expires_at: float = 0
        self.user_id: str | None = None
        self.open_id: str | None = None
        
        # Storage för persistent tokens
        storage_key = email.replace('@', '_').replace('.', '_') if email else (vin or "default")
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{storage_key}")
        
        # Standard headers
        self.headers = {
            "X-APP-ID": "ZEEKRCNCH001M0001",
            "X-PROJECT-ID": "ZEEKR_EU",
            "AppId": "ONEX97FB91F061405",
            "X-API-SIGNATURE-VERSION": "2.0",
            "X-P": "Android",
            "ACCEPT-LANGUAGE": "sv-SE",
            "X-PLATFORM": "APP",
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": "okhttp/4.12.0",
        }
    
    def _generate_request_headers(self) -> dict[str, str]:
        """Generate request-specific headers."""
        headers = self.headers.copy()
        headers.update({
            "X-API-SIGNATURE-NONCE": str(uuid.uuid4()),
            "X-TIMESTAMP": str(int(time.time() * 1000)),
            "X-DEVICE-ID": str(uuid.uuid4()),
        })
        
        if self.vin:
            headers["X-VIN"] = self.vin
            
        if self.access_token:
            headers["Authorization"] = self.access_token
            
        return headers
    
    async def async_login(self) -> bool:
        """Login and get tokens."""
        url = f"{self.base_url}/ms-user-auth/v1.0/auth/login"
        
        # Försök ladda sparade tokens först
        if await self._load_tokens():
            if await self._ensure_valid_token():
                _LOGGER.debug("Using saved tokens")
                return True
        
        _LOGGER.debug("Logging in to Zeekr API with email/password")
        
        headers = self._generate_request_headers()
        
        # Kryptera email/lösenord (enkelt base64 för demonstration)
        # I produktion skulle detta vara mer sofistikerat
        import base64
        identifier = base64.b64encode(f"{self.email}:{self.password}".encode()).decode()
        
        payload = {
            "identifier": identifier,
            "identityType": 10,  # Email/password login type
            "loginDeviceId": "homeassistant-integration",
            "loginDeviceJgId": "",
            "loginDeviceType": 1,
            "loginPhoneBrand": "homeassistant",
            "loginPhoneModel": "Integration",
            "loginSystem": "Linux",
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        _LOGGER.error("Login failed with status %s", response.status)
                        return False
                    
                    data = await response.json()
                    
                    if data.get("success") and data.get("code") == "000000":
                        self._update_tokens(data["data"])
                        await self._save_tokens()
                        _LOGGER.info("Login successful")
                        return True
                    else:
                        _LOGGER.error("Login failed: %s", data.get("msg"))
                        return False
        except Exception as err:
            _LOGGER.error("Login error: %s", err)
            return False
    
    def _update_tokens(self, data: dict[str, Any]) -> None:
        """Update tokens from API response."""
        self.access_token = data["accessToken"]
        self.refresh_token = data["refreshToken"]
        self.token_expires_at = data["expiresIn"] / 1000
        self.refresh_expires_at = data["refreshExpiresIn"] / 1000
        self.user_id = data["userId"]
        self.open_id = data["openId"]
        
        # Spara VIN om det finns i svaret
        if "vin" in data:
            self.vin = data["vin"]
    
    async def async_refresh_access_token(self) -> bool:
        """Refresh access token using refresh token."""
        if not self.refresh_token:
            _LOGGER.error("No refresh token available")
            return False
        
        if time.time() >= self.refresh_expires_at:
            _LOGGER.error("Refresh token expired")
            return False
        
        url = f"{self.base_url}/ms-user-auth/v1.0/auth/token/refresh"
        
        headers = self._generate_request_headers()
        payload = {
            "refreshToken": self.refresh_token.replace("Bearer ", "")
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        _LOGGER.error("Token refresh failed with status %s", response.status)
                        return False
                    
                    data = await response.json()
                    
                    if data.get("success") and data.get("code") == "000000":
                        self._update_tokens(data["data"])
                        await self._save_tokens()
                        _LOGGER.info("Token refreshed successfully")
                        return True
                    else:
                        _LOGGER.error("Token refresh failed: %s", data.get("msg"))
                        return False
        except Exception as err:
            _LOGGER.error("Token refresh error: %s", err)
            return False
    
    async def _ensure_valid_token(self) -> bool:
        """Ensure we have a valid token."""
        if not self.access_token:
            return False
        
        # Refresh if token expires in less than 5 minutes
        time_until_expiry = self.token_expires_at - time.time()
        
        if time_until_expiry < 300:
            _LOGGER.debug("Token expiring soon, refreshing")
            return await self.async_refresh_access_token()
        
        return True
    
    async def _save_tokens(self) -> None:
        """Save tokens to storage."""
        data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_expires_at": self.token_expires_at,
            "refresh_expires_at": self.refresh_expires_at,
            "user_id": self.user_id,
            "open_id": self.open_id,
            "vin": self.vin,
        }
        await self._store.async_save(data)
    
    async def _save_tokens_from_config(
        self, 
        access_token: str,
        refresh_token: str | None = None,
        vin: str | None = None
    ) -> None:
        """Save tokens from config (no expiry times known)."""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.vin = vin
        
        # Sätt långa expiry times (kommer uppdateras vid nästa API-anrop)
        self.token_expires_at = time.time() + (7 * 24 * 3600)  # 7 dagar
        self.refresh_expires_at = time.time() + (30 * 24 * 3600)  # 30 dagar
        
        await self._save_tokens()
    
    async def _load_tokens(self) -> bool:
        """Load tokens from storage."""
        data = await self._store.async_load()
        if not data:
            return False
        
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")
        self.token_expires_at = data.get("token_expires_at", 0)
        self.refresh_expires_at = data.get("refresh_expires_at", 0)
        self.user_id = data.get("user_id")
        self.open_id = data.get("open_id")
        self.vin = data.get("vin")
        
        return True
    
    async def async_get_vehicle_status(self) -> dict[str, Any] | None:
        """Get vehicle status."""
        if not await self._ensure_valid_token():
            _LOGGER.error("Failed to ensure valid token")
            return None
        
        # Ersätt med rätt endpoint när du vet den
        url = f"{self.base_url}/api/v1/vehicle/status"
        
        headers = self._generate_request_headers()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        _LOGGER.warning("Failed to get vehicle status: %s", response.status)
                        return None
                    
                    data = await response.json()
                    
                    if data.get("success"):
                        return data.get("data")
                    else:
                        _LOGGER.warning("Vehicle status request failed: %s", data.get("msg"))
                        return None
        except Exception as err:
            _LOGGER.error("Error getting vehicle status: %s", err)
            return None
    
    async def async_lock_doors(self) -> bool:
        """Lock vehicle doors."""
        return await self._send_command("/api/v1/vehicle/lock")
    
    async def async_unlock_doors(self) -> bool:
        """Unlock vehicle doors."""
        return await self._send_command("/api/v1/vehicle/unlock")
    
    async def async_start_climate(self, temperature: float = 21.0) -> bool:
        """Start climate control."""
        return await self._send_command(
            "/api/v1/vehicle/climate/start",
            {"temperature": temperature}
        )
    
    async def async_stop_climate(self) -> bool:
        """Stop climate control."""
        return await self._send_command("/api/v1/vehicle/climate/stop")
    
    async def _send_command(self, endpoint: str, data: dict[str, Any] | None = None) -> bool:
        """Send command to vehicle."""
        if not await self._ensure_valid_token():
            _LOGGER.error("Failed to ensure valid token")
            return False
        
        url = f"{self.base_url}{endpoint}"
        headers = self._generate_request_headers()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data or {}) as response:
                    if response.status != 200:
                        _LOGGER.error("Command failed with status %s", response.status)
                        return False
                    
                    result = await response.json()
                    return result.get("success", False)
        except Exception as err:
            _LOGGER.error("Command error: %s", err)
            return False
