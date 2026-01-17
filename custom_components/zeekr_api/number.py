import logging
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, URL_CHARGE_CONTROL, URL_CONTROL

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    prefix = coordinator.entry.data.get('name', 'Zeekr 7X')
    
    entities = [
        ZeekrChargeLimit(coordinator, entry),
        # Seat Heating
        ZeekrSeatHeating(coordinator, prefix, "driver", "main_driver_seat", "seat_heating_driver"),
        ZeekrSeatHeating(coordinator, prefix, "passenger", "copilot_seat", "seat_heating_passenger"),
        ZeekrSeatHeating(coordinator, prefix, "rear_left", "second_row_left", "seat_heating_rear_left"),
        ZeekrSeatHeating(coordinator, prefix, "rear_right", "second_row_right", "seat_heating_rear_right"),
        # Seat Ventilation (front seats only)
        ZeekrSeatVentilation(coordinator, prefix, "driver", "main_driver_seat", "seat_ventilation_driver"),
        ZeekrSeatVentilation(coordinator, prefix, "passenger", "copilot_seat", "seat_ventilation_passenger"),
    ]
    
    async_add_entities(entities)

class ZeekrChargeLimit(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.entry = entry
        prefix = coordinator.entry.data.get('name', 'Zeekr 7X')
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "charge_limit"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_charge_limit"
        self._attr_native_min_value = 50
        self._attr_native_max_value = 100
        self._attr_native_step = 1
        self._attr_native_unit_of_measurement = "%"
        self._attr_icon = "mdi:battery-charging-80"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
            "model": "7X",
        }

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

        await self.coordinator.send_command(
            URL_CHARGE_CONTROL, 
            payload, 
            f"Laadlimiet instellen op {value}% ({api_value})"
        )
        
        self.async_write_ha_state()


class ZeekrSeatHeating(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, prefix, position_name, api_position, translation_key):
        super().__init__(coordinator)
        self.api_position = api_position
        self.position_name = position_name
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{translation_key}"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 3
        self._attr_native_step = 1
        self._attr_icon = "mdi:car-seat-heater"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    @property
    def native_value(self):
        # TODO: Read actual level from API when available
        return 0

    async def async_set_native_value(self, value):
        level = int(value)
        
        # Map position based on Proxyman discovery
        position_map = {
            "main_driver_seat": "11",      # Confirmed via Proxyman
            "copilot_seat": "12",          # Confirmed via Proxyman  
            "second_row_left": "21",       # Confirmed via Proxyman
            "second_row_right": "29"       # Confirmed via Proxyman ⬅️ .29 not .22!
        }
        
        seat_num = position_map.get(self.api_position, "11")
        
        if level == 0:
            # Turn off
            payload = {
                "command": "start",
                "serviceId": "ZAF",
                "setting": {
                    "serviceParameters": [
                        {"key": f"SH.{seat_num}", "value": "false"}
                    ]
                }
            }
        else:
            # Set level with duration (15 min like in app)
            payload = {
                "command": "start",
                "serviceId": "ZAF",
                "setting": {
                    "serviceParameters": [
                        {"key": f"SH.{seat_num}", "value": "true"},
                        {"key": f"SH.{seat_num}.level", "value": str(level)},
                        {"key": f"SH.{seat_num}.duration", "value": "15"}
                    ]
                }
            }
        
        await self.coordinator.send_command(
            URL_CONTROL, 
            payload, 
            f"Stoelverwarming {self.position_name} niveau {level}"
        )


class ZeekrSeatVentilation(CoordinatorEntity, NumberEntity):
    def __init__(self, coordinator, prefix, position_name, api_position, translation_key):
        super().__init__(coordinator)
        self.api_position = api_position
        self.position_name = position_name
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{translation_key}"
        self._attr_native_min_value = 0
        self._attr_native_max_value = 3
        self._attr_native_step = 1
        self._attr_icon = "mdi:car-seat-cooler"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    @property
    def native_value(self):
        # TODO: Read actual level from API when available
        return 0

    async def async_set_native_value(self, value):
        level = int(value)
        
        # Map position for front seats only (no rear ventilation)
        position_map = {
            "main_driver_seat": "11",
            "copilot_seat": "12"
        }
        
        seat_num = position_map.get(self.api_position, "11")
        
        if level == 0:
            # Turn off
            payload = {
                "command": "start",
                "serviceId": "ZAF",
                "setting": {
                    "serviceParameters": [
                        {"key": f"SV.{seat_num}", "value": "false"}
                    ]
                }
            }
        else:
            # Set level with duration (15 min like in app)
            payload = {
                "command": "start",
                "serviceId": "ZAF",
                "setting": {
                    "serviceParameters": [
                        {"key": f"SV.{seat_num}", "value": "true"},
                        {"key": f"SV.{seat_num}.level", "value": str(level)},
                        {"key": f"SV.{seat_num}.duration", "value": "15"}
                    ]
                }
            }
        
        await self.coordinator.send_command(
            URL_CONTROL, 
            payload, 
            f"Stoelventilatie {self.position_name} niveau {level}"
        )


        
        await self.coordinator.send_command(
            URL_CONTROL, 
            payload, 
            f"Stuurverwarming niveau {level}"
        )
