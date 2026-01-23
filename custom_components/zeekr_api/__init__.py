import asyncio
from datetime import timedelta
import logging
import aiohttp
import hmac
import hashlib
import base64
from urllib.parse import urlparse, parse_qs
import uuid
import time as time_module
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, PLATFORMS, URL_STATUS, URL_SENTRY, URL_TRAVEL, URL_LIST, URL_QRVS, URL_SOC, URL_CHARGE_PLAN

_LOGGER = logging.getLogger(__name__)

# ============================================================================
# APP SECRET - SET YOUR SECRET HERE WHEN YOU FIND IT!
# ============================================================================
# When you obtain app_secret from Frida or another method, replace this line:
APP_SECRET = "YOUR_APP_SECRET_HERE"  # <-- CHANGE THIS!

# If you find the secret, change to for example:
# APP_SECRET = "JDEkMCQ1ZWVlNjUxYWJjNDI3MTU1MjE5OTZhNzlmYjQyNzRjZjQwZGQ4ODM0NDNjMzkxZjU2Yzk5OGY1ZmZkOTZiNmY0"
# ============================================================================


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    coordinator = ZeekrCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok: 
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class ZeekrCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_method=self._async_update_data, update_interval=timedelta(minutes=15))
        self.entry = entry

    def _generate_signature(self, method: str, url: str, headers: dict, body: str = "") -> str:
        """
        Generate HMAC-SHA256 signature for Zeekr API v2.0
        
        Based on reverse engineering of com.baselinelibrary.sign.SignUtil.sign()
        """
        # Check if we have the secret
        if APP_SECRET == "YOUR_APP_SECRET_HERE":
            _LOGGER.warning("APP_SECRET not set! Signature will not work. Set APP_SECRET in __init__.py")
            return ""
        
        # Parse URL
        parsed = urlparse(url)
        path = parsed.path
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        
        # Build headers part (Accept + X-api* headers, sorted lowercase)
        headers_part = ""
        api_headers = {}
        
        # Add Accept header if present
        if "Accept" in headers:
            headers_part += f"{headers['Accept'].strip()}\n"
        
        # Collect X-api* headers
        for key, value in headers.items():
            if key.lower().startswith("x-api"):
                api_headers[key] = value
        
        # Sort and add X-api* headers
        for key in sorted(api_headers.keys()):
            headers_part += f"{key.lower().strip()}:{api_headers[key].strip()}\n"
        
        # Build query params part (sorted, URL-encoded)
        params_part = ""
        if query_params:
            sorted_params = []
            for key in sorted(query_params.keys()):
                value = query_params[key][0] if query_params[key] else ""
                # URL encode special characters
                value = value.replace(" ", "%20").replace("*", "%2A").replace(",", "%2C")
                sorted_params.append(f"{key}={value}")
            params_part = "&".join(sorted_params)
        
        # Build body part (MD5 hash in base64)
        if body:
            body_hash = hashlib.md5(body.encode('utf-8')).digest()
            body_md5 = base64.b64encode(body_hash).decode('utf-8')
        else:
            body_md5 = ""
        
        # Get timestamp from headers
        timestamp = headers.get("X-TIMESTAMP", headers.get("X-Timestamp", ""))
        
        # Build signature string
        signature_string = (
            f"{headers_part}\n"
            f"{params_part}\n"
            f"{body_md5}{timestamp}\n"
            f"{method}\n"
            f"{path}"
        )
        
        # Generate HMAC-SHA256 signature
        try:
            signature = hmac.new(
                APP_SECRET.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha256
            ).digest()
            
            return base64.b64encode(signature).decode('utf-8')
        except Exception as e:
            _LOGGER.error(f"Error generating signature: {e}")
            return ""

    def _get_signature_headers(self, method: str, url: str, body: str = "") -> dict:
        """
        Generate all required headers including signature for API v2.0
        """
        timestamp = str(int(time_module.time() * 1000))
        nonce = str(uuid.uuid4())
        
        # Base headers needed for signature calculation
        headers = {
            "X-API-SIGNATURE-NONCE": nonce,
            "X-API-SIGNATURE-VERSION": "2.0",
            "X-TIMESTAMP": timestamp,
        }
        
        # Calculate signature
        signature = self._generate_signature(method, url, headers, body)
        
        # Return complete headers
        return {
            "X-APP-ID": "ZEEKRCNCH001M0001",
            "X-PROJECT-ID": "ZEEKR_EU",
            "AppId": "ONEX97FB91F061405",
            "X-API-SIGNATURE-VERSION": "2.0",
            "X-API-SIGNATURE-NONCE": nonce,
            "X-TIMESTAMP": timestamp,
            "X-SIGNATURE": signature,
            "Content-Type": "application/json;charset=UTF-8",
        }

    async def _get_valid_token(self):
        """Get the token."""
        token = self.entry.data.get("access_token")
        if not token: 
            return ""
        return f"Bearer {token}" if not token.startswith("Bearer ") else token

    async def _async_update_data(self):
        """Fetch all data from the different Zeekr endpoints."""
        token = await self._get_valid_token()
        vin = self.entry.data.get('vin')
        
        # Check if we should use signature authentication or token-only
        use_signature = APP_SECRET != "YOUR_APP_SECRET_HERE"
        
        if use_signature:
            _LOGGER.info("Using signature-based authentication")
            # For GET requests with signature
            base_headers = {
                "Authorization": token,
                "X-VIN": vin,
            }
        else:
            _LOGGER.warning("APP_SECRET not set - using token-only authentication (may not work for all endpoints)")
            base_headers = {
                "Authorization": token,
                "X-VIN": vin,
                "X-APP-ID": "ZEEKRCNCH001M0001",
                "X-PROJECT-ID": "ZEEKR_EU",
                "Content-Type": "application/json"
            }

        endpoints = [
            URL_STATUS,      # 0
            URL_QRVS,        # 1
            URL_CHARGE_PLAN, # 2
            URL_SOC,         # 3
            URL_TRAVEL,      # 4
            URL_SENTRY,      # 5
            URL_LIST         # 6
        ]

        try:
            async with aiohttp.ClientSession() as session:
                tasks = []
                for url in endpoints:
                    if use_signature:
                        # Add signature headers for each request
                        sig_headers = self._get_signature_headers("GET", url)
                        headers = {**base_headers, **sig_headers}
                    else:
                        headers = base_headers
                    
                    tasks.append(session.get(url, headers=headers, timeout=15))
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                raw_results = []
                for resp in responses:
                    if not isinstance(resp, Exception) and resp.status == 200:
                        json_res = await resp.json()
                        raw_results.append(json_res)
                    else:
                        raw_results.append({})

                # Helper function to safely 'data' retrieve
                def get_data(res):
                    if isinstance(res, dict):
                        return res.get("data", res)
                    return res

                # Mapping of results
                status_data = get_data(raw_results[0])
                list_res = raw_results[6]

                # Search for vehicle info
                vehicle_info = {}
                search_list = []
                if isinstance(list_res, dict):
                    d = list_res.get("data", [])
                    if isinstance(d, list):
                        search_list = d
                    elif isinstance(d, dict):
                        search_list = d.get("vehicleInfoList", [])
                elif isinstance(list_res, list):
                    search_list = list_res

                # Find the correct car based on VIN
                for v in search_list:
                    if isinstance(v, dict) and v.get("vin") == vin:
                        vehicle_info = v
                        break
                
                # If no match on VIN, take the first as fallback
                if not vehicle_info and search_list:
                    vehicle_info = search_list[0]

                return {
                    "main": status_data if isinstance(status_data, dict) else {},
                    "qrvs": get_data(raw_results[1]) if raw_results[1] else {},
                    "plan": get_data(raw_results[2]) if raw_results[2] else {},
                    "soc_limit": get_data(raw_results[3]) if raw_results[3] else {},
                    "travel": get_data(raw_results[4]) if raw_results[4] else {},
                    "sentry": get_data(raw_results[5]) if raw_results[5] else {},
                    "info": vehicle_info if isinstance(vehicle_info, dict) else {}
                }

        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")

    async def send_command(self, url, payload, description=""):
        """Send command to Zeekr API with signature"""
        token = self.entry.data.get("access_token")
        vin = self.entry.data.get("vin")
        
        # Convert payload to JSON string for signature
        import json
        body = json.dumps(payload)
        
        # Check if we should use signature
        use_signature = APP_SECRET != "YOUR_APP_SECRET_HERE"
        
        if use_signature:
            # Generate signature headers
            sig_headers = self._get_signature_headers("POST", url, body)
            
            headers = {
                "Authorization": token if token.startswith("Bearer ") else f"Bearer {token}",
                "X-VIN": vin,
                **sig_headers
            }
        else:
            _LOGGER.warning(f"Sending command without signature - may fail: {description}")
            headers = {
                "Authorization": token if token.startswith("Bearer ") else f"Bearer {token}",
                "X-VIN": vin,
                "X-APP-ID": "ZEEKRCNCH001M0001",
                "X-PROJECT-ID": "ZEEKR_EU",
                "Content-Type": "application/json;charset=utf-8"
            }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=10) as resp:
                    response_text = await resp.text()
                    _LOGGER.warning(f"🔵 Response status: {resp.status}")
                    _LOGGER.warning(f"🔵 Response body: {response_text[:500]}")
                    
                    if resp.status == 200:
                        try:
                            response_data = await resp.json()
                            _LOGGER.info(f"OK: {description}")
                            await asyncio.sleep(5)
                            await self.async_request_refresh()
                            return response_data  # Return response for session handling
                        except:
                            _LOGGER.info(f"OK: {description}")
                            await asyncio.sleep(5)
                            await self.async_request_refresh()
                            return None
                    else: 
                        _LOGGER.error(f"Error {resp.status} bij {description}: {response_text}")
                        return None
        except Exception as e:
            _LOGGER.error(f"Error with {description}: {e}")
            return None
