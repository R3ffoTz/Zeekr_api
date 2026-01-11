import logging
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, URL_CHARGE_CONTROL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ZeekrChargeLimit(coordinator, entry)])

class ZeekrChargeLimit(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        prefix = coordinator.entry.data.get('name', 'Zeekr 7X')
        vin = coordinator.entry.data.get('vin')
        self._attr_name = f"{prefix} Laadlimiet"
        self._attr_unique_id = f"{entry.entry_id}_charge_limit"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
            "model": "7X",
            }
        self._attr_native_min_value = 50
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "%"
        self._attr_icon = "mdi:battery-charging-80"

    @property
    def native_value(self):
        soc_data = self.coordinator.data.get("soc_limit", {})
        
        val = soc_data.get("soc")
        
        try:
            if val is None:
                return 60
            
            num = int(float(val))
            # Omdat de API met factor 10 werkt (900 = 90%), corrigeren we dit voor de slider
            if num >= 100:
                return num / 10
            return float(num)
        except (ValueError, TypeError):
            return 70

    async def async_set_native_value(self, value):
        api_value = str(int(value * 10))
        
        payload = {
            "command": "start",
            "serviceId": "RCS",
            "setting": {
                "serviceParameters": [
                    {
                        "key": "soc", 
                        "value": api_value
                    },
                    {
                        "key": "rcs.setting", 
                        "value": "1"
                    },
                    {
                        "key": "altCurrent", 
                        "value": "1"
                    }
                ]
            }
        }

        # Verstuur naar de gecorrigeerde URL_CHARGE_CONTROL
        await self.coordinator.send_command(
            URL_CHARGE_CONTROL, 
            payload, 
            f"Laadlimiet instellen op {value}% ({api_value})"
        )
        
        # Update de status direct in de UI
        self.async_write_ha_state()