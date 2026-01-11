import asyncio
from datetime import timedelta
import logging
import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, PLATFORMS, URL_STATUS, URL_SENTRY, URL_TRAVEL, URL_LIST, URL_QRVS, URL_SOC, URL_CHARGE_PLAN
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    coordinator = ZeekrCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok: hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

class ZeekrCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=30))
        self.entry = entry

    async def _get_valid_token(self):
        """Haal het token op."""
        token = self.entry.data.get("access_token")
        if not token: return ""
        return f"Bearer {token}" if not token.startswith("Bearer ") else token

    async def _async_update_data(self):
        """Haal alle data op van de verschillende Zeekr endpoints."""
        token = await self._get_valid_token()
        vin = self.entry.data.get('vin')
        
        headers = {
            "Authorization": f"Bearer {token}" if not token.startswith("Bearer ") else token,
            "X-VIN": vin,
            "X-APP-ID": "ZEEKRCNCH001M0001",
            "X-PROJECT-ID": "ZEEKR_EU",
            "Content-Type": "application/json"
        }

        # We definiëren de taken voor asyncio.gather
        # De volgorde is belangrijk voor het uitpakken later
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
                        # Belangrijk: we slaan de hele response op, 
                        # zodat we later kunnen checken of 'data' een dict of lijst is.
                        raw_results.append(json_res)
                    else:
                        raw_results.append({})

                # Helper functie om veilig 'data' op te halen
                def get_data(res):
                    if isinstance(res, dict):
                        return res.get("data", res)
                    return res

                # Mappen van resultaten
                status_data = get_data(raw_results[0])
                list_res = raw_results[6] # De volledige response van de voertuiglijst

                # Voertuig info zoeken (BFF API geeft vaak direct een lijst in 'data')
                vehicle_info = {}
                # We halen de lijst op: uit .get("data") of de root
                search_list = []
                if isinstance(list_res, dict):
                    d = list_res.get("data", [])
                    if isinstance(d, list):
                        search_list = d
                    elif isinstance(d, dict):
                        search_list = d.get("vehicleInfoList", [])
                elif isinstance(list_res, list):
                    search_list = list_res

                # Zoek de juiste auto op basis van VIN
                for v in search_list:
                    if isinstance(v, dict) and v.get("vin") == vin:
                        vehicle_info = v
                        break
                
                # Als er geen match is op VIN, pak dan de eerste als fallback
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
            raise UpdateFailed(f"Fout bij ophalen data: {err}")

    async def send_command(self, url, payload, description=""):
        token = self.entry.data.get("access_token")
        headers = {
            "Authorization": token if token.startswith("Bearer ") else f"Bearer {token}",
            "X-VIN": self.entry.data.get("vin"), 
            "X-APP-ID": "ZEEKRCNCH001M0001",  # VERPLICHT voor commando's
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
                    else: 
                        _LOGGER.error(f"Fout {resp.status} bij {description}: {await resp.text()}")
        except Exception as e:
            _LOGGER.error(f"Fout bij {description}: {e}")