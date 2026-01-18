from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, URL_CONTROL
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    prefix = entry.data.get("name", "Zeekr")
    
    async_add_entities([
        ZeekrRefreshButton(coordinator, prefix),
        ZeekrTrunkButton(coordinator, prefix),
        ZeekrTravelUpdateButton(coordinator, prefix, entry.entry_id),
        ZeekrHoodButton(coordinator, prefix),
        ZeekrWindowVentilationButton(coordinator, prefix),
        ZeekrWindowDownButton(coordinator, prefix),
        ZeekrWindowUpButton(coordinator, prefix),
        ZeekrFlashLightsButton(coordinator, prefix),
        ZeekrHonkFlashButton(coordinator, prefix),
        ZeekrParkingComfortDisableButton(coordinator, prefix),
    ])

class ZeekrTravelUpdateButton(ButtonEntity):
    def __init__(self, coordinator, prefix, entry_id):
        self.coordinator = coordinator
        vin = coordinator.entry.data.get('vin')
        self._entry_id = entry_id
        
        self._attr_translation_key = "update_travel_plan"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry_id}_travel_update"
        self._attr_icon = "mdi:cloud-upload"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    async def async_press(self):
        travel_switch = self.hass.data[DOMAIN].get(f"{self._entry_id}_travel_switch")
        if travel_switch:
            await travel_switch._send_plan("start")
        else:
            _LOGGER.error("Travel Switch niet gevonden")

class ZeekrRefreshButton(ButtonEntity):
    def __init__(self, coordinator, prefix):
        self.coordinator = coordinator
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "refresh_data"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_refresh_button"
        self._attr_icon = "mdi:database-refresh"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    async def async_press(self):
        await self.coordinator.async_refresh()

class ZeekrTrunkButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "open_trunk"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_trunk_button"
        self._attr_icon = "mdi:car-back"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    async def async_press(self):
        payload = {
            "command": "start",
            "serviceId": "RDU",
            "setting": {
                "serviceParameters": [
                    {
                        "key": "target",
                        "value": "trunk"
                    }
                ]
            }
        }

        await self.coordinator.send_command(URL_CONTROL, payload, "Achterklep openen")


class ZeekrHoodButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "open_hood"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_hood_button"
        self._attr_icon = "mdi:car-front"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    async def async_press(self):
        payload = {
            "command": "start",
            "serviceId": "RDU",
            "setting": {
                "serviceParameters": [
                    {
                        "key": "target",
                        "value": "hood"
                    }
                ]
            }
        }
        await self.coordinator.send_command(URL_CONTROL, payload, "Motorhuv openen")


class ZeekrWindowVentilationButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "window_ventilation"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_window_ventilation"
        self._attr_icon = "mdi:window-open-variant"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    async def async_press(self):
        payload = {
            "command": "start",
            "serviceId": "RWS",
            "setting": {
                "serviceParameters": [
                    {
                        "key": "target",
                        "value": "ventilate"
                    }
                ]
            }
        }
        await self.coordinator.send_command(URL_CONTROL, payload, "Raam ventilatie")


class ZeekrWindowDownButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "window_down"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_window_down"
        self._attr_icon = "mdi:window-open"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    async def async_press(self):
        payload = {
            "command": "start",
            "serviceId": "RWS",
            "setting": {
                "serviceParameters": [
                    {
                        "key": "target",
                        "value": "window"
                    }
                ]
            }
        }
        await self.coordinator.send_command(URL_CONTROL, payload, "Fönster helt ner")


class ZeekrWindowUpButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "window_up"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_window_up"
        self._attr_icon = "mdi:window-closed"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    async def async_press(self):
        payload = {
            "command": "stop",
            "serviceId": "RWS",
            "setting": {
                "serviceParameters": [
                    {
                        "key": "target",
                        "value": "window"
                    }
                ]
            }
        }
        await self.coordinator.send_command(URL_CONTROL, payload, "Stäng fönster")


class ZeekrFlashLightsButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "flash_lights"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_flash_lights"
        self._attr_icon = "mdi:car-light-alert"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    async def async_press(self):
        payload = {
            "command": "start",
            "serviceId": "RHL",
            "setting": {
                "serviceParameters": [
                    {
                        "key": "rhl",
                        "value": "light-flash"
                    }
                ]
            }
        }
        await self.coordinator.send_command(URL_CONTROL, payload, "Flash lights")


class ZeekrHonkFlashButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "honk_and_flash"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_honk_and_flash"
        self._attr_icon = "mdi:bullhorn"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    async def async_press(self):
        payload = {
            "command": "start",
            "serviceId": "RHL",
            "setting": {
                "serviceParameters": [
                    {
                        "key": "rhl",
                        "value": "horn-light-flash"
                    }
                ]
            }
        }
        await self.coordinator.send_command(URL_CONTROL, payload, "Honk and flash")


class ZeekrParkingComfortDisableButton(CoordinatorEntity, ButtonEntity):
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "disable_parking_comfort"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_disable_parking_comfort"
        self._attr_icon = "mdi:car-seat-cooler"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    async def async_press(self):
        payload = {
            "command": "stop",
            "serviceId": "PCM",
            "setting": {
                "serviceParameters": [
                    {
                        "key": "parking_comfortable",
                        "value": "false"
                    }
                ]
            }
        }
        await self.coordinator.send_command(URL_CONTROL, payload, "Disable parking comfort")
