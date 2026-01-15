import asyncio
from datetime import timedelta
import logging
import aiohttp
import time as python_time
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed
from .const import DOMAIN, PLATFORMS, URL_STATUS, URL_SENTRY, URL_TRAVEL, URL_LIST, URL_QRVS, URL_SOC, URL_CHARGE_PLAN, URL_LOGIN

_LOGGER = logging.getLogger(__name__)

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
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(minutes=15))
        self.entry = entry
        self._token_refresh_lock = asyncio.Lock()

    async def _check_and_refresh_token(self):
        """Kontrollera om token behöver förnyas och förnya vid behov."""
        async with self._token_refresh_lock:
            current_time = python_time.time()
            expires_at = self.entry.data.get("expires_at", 0)
            
            # Förnya token om den går ut inom 24 timmar (86400 sekunder)
            if expires_at - current_time < 86400:
                _LOGGER.info("Token går snart ut, försöker förnya...")
                try:
                    await self._refresh_token()
                except Exception as e:
                    _LOGGER.error(f"Kunde inte förnya token: {e}")
                    # Om vi inte kan förnya och token redan är utgången, kasta fel
                    if current_time >= expires_at:
                        raise ConfigEntryAuthFailed("Token har gått ut och kunde inte förnyas")

    async def _refresh_token(self):
        """Förnya access token med hjälp av refresh token."""
        refresh_token = self.entry.data.get("refresh_token")
        identifier = self.entry.data.get("identifier")
        vin = self.entry.data.get("vin")
        
        if not refresh_token or not identifier:
            _LOGGER.error("Saknar refresh_token eller identifier för token-förnyelse")
            raise ConfigEntryAuthFailed("Kan inte förnya token - saknar credentials")
        
        headers = {
            "X-APP-ID": "ZEEKRCNCH001M0001",
            "X-PROJECT-ID": "ZEEKR_EU",
            "AppId": "ONEX97FB91F061405",
            "X-API-SIGNATURE-VERSION": "2.0",
            "X-P": "Android",
            "ACCEPT-LANGUAGE": "sv-SE",
            "X-API-SIGNATURE-NONCE": self._generate_nonce(),
            "X-TIMESTAMP": str(int(python_time.time() * 1000)),
            "X-DEVICE-ID": self.entry.data.get("device_id", "homeassistant-integration"),
            "X-PLATFORM": "APP",
            "Authorization": f"Bearer {refresh_token}" if not refresh_token.startswith("Bearer ") else refresh_token,
            "X-VIN": vin,
            "Content-Type": "application/json; charset=UTF-8"
        }
        
        payload = {
            "identifier": identifier,
            "identityType": 10,
            "loginDeviceId": self.entry.data.get("device_id", "homeassistant-integration"),
            "loginDeviceJgId": "",
            "loginDeviceType": 1,
            "loginPhoneBrand": "homeassistant",
            "loginPhoneModel": "integration",
            "loginSystem": "Linux"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(URL_LOGIN, json=payload, headers=headers, timeout=15) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        
                        if result.get("success") and result.get("data"):
                            data = result["data"]
                            new_access_token = data.get("accessToken", "").replace("Bearer ", "")
                            new_refresh_token = data.get("refreshToken", "")
                            expires_in = data.get("expiresIn", 0)
                            
                            # Uppdatera config entry med nya tokens
                            self.hass.config_entries.async_update_entry(
                                self.entry,
                                data={
                                    **self.entry.data,
                                    "access_token": new_access_token,
                                    "refresh_token": new_refresh_token,
                                    "expires_at": expires_in / 1000 if expires_in > 0 else python_time.time() + 604800,
                                    "refresh_expires_at": data.get("refreshExpiresIn", 0) / 1000
                                }
                            )
                            
                            _LOGGER.info("Token förnyades framgångsrikt")
                        else:
                            raise Exception(f"Token-förnyelse misslyckades: {result.get('msg', 'Unknown error')}")
                    else:
                        error_text = await resp.text()
                        raise Exception(f"HTTP {resp.status}: {error_text}")
                        
        except Exception as e:
            _LOGGER.error(f"Fel vid token-förnyelse: {e}")
            raise

    def _generate_nonce(self):
        """Generera ett UUID för nonce."""
        import uuid
        return str(uuid.uuid4())

    async def _get_valid_token(self):
        """Hämta giltig token, förnya om nödvändigt."""
        await self._check_and_refresh_token()
        token = self.entry.data.get("access_token")
        if not token: 
            return ""
        return f"Bearer {token}" if not token.startswith("Bearer ") else token

    async def _async_update_data(self):
        """Hämta alla data från de olika Zeekr endpoints."""
        try:
            token = await self._get_valid_token()
        except ConfigEntryAuthFailed:
            _LOGGER.error("Token har gått ut och kunde inte förnyas. Använd Reconfigure för att logga in igen.")
            raise UpdateFailed("Token har gått ut - vänligen konfigurera om integrationen")
            
        vin = self.entry.data.get('vin')
        
        headers = {
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
            async with aiohttp.ClientSession(headers=headers) as session:
                tasks = [session.get(url, timeout=15) for url in endpoints]
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                raw_results = []
                for resp in responses:
                    if not isinstance(resp, Exception) and resp.status == 200:
                        json_res = await resp.json()
                        raw_results.append(json_res)
                    elif not isinstance(resp, Exception) and resp.status in [401, 403]:
                        # Token kanske har gått ut trots kontroll
                        _LOGGER.warning(f"Fick {resp.status} - försöker förnya token...")
                        await self._refresh_token()
                        raise UpdateFailed("Token förnyad - försöker igen vid nästa uppdatering")
                    else:
                        raw_results.append({})

                def get_data(res):
                    if isinstance(res, dict):
                        return res.get("data", res)
                    return res

                status_data = get_data(raw_results[0])
                list_res = raw_results[6]

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

                for v in search_list:
                    if isinstance(v, dict) and v.get("vin") == vin:
                        vehicle_info = v
                        break
                
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
            raise UpdateFailed(f"Fel vid hämtning av data: {err}")

    async def send_command(self, url, payload, description=""):
        """Skicka kommando till bilen."""
        try:
            token = await self._get_valid_token()
        except ConfigEntryAuthFailed:
            _LOGGER.error("Token har gått ut - kan inte skicka kommando")
            return
            
        headers = {
            "Authorization": token,
            "X-VIN": self.entry.data.get("vin"), 
            "X-APP-ID": "ZEEKRCNCH001M0001",
            "X-PROJECT-ID": "ZEEKR_EU",
            "Content-Type": "application/json;charset=utf-8"
        }
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(url, json=payload, timeout=10) as resp:
                    if resp.status == 200: 
                        _LOGGER.info(f"OK: {description}")
                        await asyncio.sleep(5)
                        await self.async_request_refresh()
                    elif resp.status in [401, 403]:
                        _LOGGER.warning(f"Token utgången vid {description} - försöker förnya...")
                        await self._refresh_token()
                        # Försök igen med ny token
                        token = await self._get_valid_token()
                        headers["Authorization"] = token
                        async with session.post(url, json=payload, timeout=10) as retry_resp:
                            if retry_resp.status == 200:
                                _LOGGER.info(f"OK efter token-förnyelse: {description}")
                                await asyncio.sleep(5)
                                await self.async_request_refresh()
                            else:
                                _LOGGER.error(f"Fel {retry_resp.status} efter retry för {description}")
                    else: 
                        _LOGGER.error(f"Fel {resp.status} för {description}: {await resp.text()}")
        except Exception as e:
            _LOGGER.error(f"Fel vid {description}: {e}")
