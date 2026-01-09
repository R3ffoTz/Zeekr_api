import asyncio
from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.const import UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, URL_CONTROL

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZeekrClimate(coordinator)])

class ZeekrClimate(CoordinatorEntity, ClimateEntity):
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT_COOL]
    _attr_preset_modes = ["Standaard", "Snel Verwarmen", "Snel Koelen"]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | 
        ClimateEntityFeature.TURN_ON | 
        ClimateEntityFeature.TURN_OFF |
        ClimateEntityFeature.PRESET_MODE
    )
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 16.0
    _attr_max_temp = 28.0

    def __init__(self, coordinator):
        super().__init__(coordinator)
        prefix = coordinator.entry.data.get("name", "Zeekr 7X")
        vin = coordinator.entry.data.get('vin')
        self._attr_name = f"{prefix} Thermostaat"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_climate"
        self._target_temp = 20.0 
        self._attr_preset_mode = "Standaard"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }
    @property
    def hvac_mode(self):
        status = self.coordinator.data.get("main", {}).get("additionalVehicleStatus", {}).get("climateStatus", {})
        return HVACMode.HEAT_COOL if status.get("preClimateActive") is True else HVACMode.OFF

    @property
    def current_temperature(self):
        temp = self.coordinator.data.get("main", {}).get("additionalVehicleStatus", {}).get("climateStatus", {}).get("interiorTemp")
        try: return float(temp) if temp else None
        except: return None

    @property
    def target_temperature(self): return self._target_temp

    async def async_set_hvac_mode(self, hvac_mode):
        if hvac_mode == HVACMode.OFF: await self.async_turn_off()
        else: await self.async_turn_on()

    async def async_set_temperature(self, **kwargs):
        if (temp := kwargs.get("temperature")) is not None:
            self._target_temp = temp
            if self.hvac_mode != HVACMode.OFF:
                await self._send_climate_command(True, temp)

    async def async_set_preset_mode(self, preset_mode):
        self._attr_preset_mode = preset_mode
        if preset_mode == "Snel Verwarmen": await self._send_climate_command(True, 28.5)
        elif preset_mode == "Snel Koelen": await self._send_climate_command(True, 15.5)
        else: await self.async_turn_on()

    async def async_turn_on(self, **kwargs):
        temp = kwargs.get("temperature", self._target_temp)
        await self._send_climate_command(True, temp)

    async def async_turn_off(self, **kwargs):
        await self._send_climate_command(False)

    async def _send_climate_command(self, active, temp=None):
        payload = {"command": "start", "serviceId": "ZAF", "setting": {"serviceParameters": [{"key": "AC", "value": "true" if active else "false"}]}}
        if active and temp:
            payload["setting"]["serviceParameters"].extend([{"key": "AC.temp", "value": str(temp)}, {"key": "AC.duration", "value": "15"}])

        await self.coordinator.send_command(URL_CONTROL, payload, f"Klimaat {'Aan' if active else 'Uit'}")
