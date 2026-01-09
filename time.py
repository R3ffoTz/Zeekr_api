from homeassistant.components.time import TimeEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from datetime import time
from .const import DOMAIN, URL_CHARGE_PLAN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    prefix = entry.data.get("name", "Zeekr")
    dagnamen = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
    
    entities = [
        ZeekrChargeTime(coordinator, entry, "start"),
        ZeekrChargeTime(coordinator, entry, "end")
    ]
    for i, dagnaam in enumerate(dagnamen, 1):
        entities.append(ZeekrTravelTime(coordinator, prefix, i, dagnaam, entry.entry_id))
        
    async_add_entities(entities)

class ZeekrTravelTime(CoordinatorEntity, TimeEntity):
    def __init__(self, coordinator, prefix, day_num, day_name, entry_id):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        self.day_index = day_num
        self._attr_name = f"{prefix} {day_name} Tijd"
        self._attr_unique_id = f"{entry_id}_travel_day_{day_num}_time"
        self._attr_icon = "mdi:clock-outline"
        self._local_time = None
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    @property
    def native_value(self) -> time:
        if self._local_time: return self._local_time
        plans = self.coordinator.data.get("travel", {}).get("scheduleList", [])
        for p in plans:
            if str(p.get("day")) == str(self.day_index):
                try:
                    h, m = map(int, p.get("startTime", "08:00").split(':'))
                    return time(h, m)
                except: pass
        return time(8, 0)

    async def async_set_value(self, value: time) -> None:
        self._local_time = value
        self.async_write_ha_state()

class ZeekrChargeTime(CoordinatorEntity, TimeEntity):
    def __init__(self, coordinator, entry, time_type):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        prefix = coordinator.entry.data.get('name', 'Zeekr')
        self.entry = entry
        self.time_type = time_type
        self._attr_name = f"{coordinator.entry.data.get('name', 'Zeekr')} Laadplan {time_type.capitalize()}tijd"
        self._attr_unique_id = f"{entry.entry_id}_charge_{time_type}_time"
        self._attr_icon = "mdi:clock-start" if time_type == "start" else "mdi:clock-end"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    @property
    def native_value(self) -> time:
        plan = self.coordinator.data.get("plan", {})
        key = "startTime" if self.time_type == "start" else "endTime"
        time_str = plan.get(key, "00:00")
        try:
            h, m = map(int, time_str.split(':'))
            return time(h, m)
        except: return time(0, 0)

    async def async_set_value(self, value: time) -> None:
        new_time = value.strftime("%H:%M")
        plan = self.coordinator.data.get("plan", {})
        start = new_time if self.time_type == "start" else plan.get("startTime", "01:15")
        end = new_time if self.time_type == "end" else plan.get("endTime", "06:45")
        payload = {"target": 2, "endTime": end, "timerId": "2", "startTime": start, "command": "start"}
        await self.coordinator.send_command(URL_CHARGE_PLAN, payload, f"Laadplan gewijzigd")