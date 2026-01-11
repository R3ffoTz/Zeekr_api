from homeassistant.components.time import TimeEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from datetime import time
import datetime
from .const import DOMAIN, URL_CHARGE_PLAN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    prefix = entry.data.get("name", "Zeekr 7X")

    entities = [
        ZeekrChargeTime(coordinator, entry, "start"),
        ZeekrChargeTime(coordinator, entry, "end")
    ]
    entities.append(ZeekrTravelTime(coordinator, prefix, 0, "Reisplan", entry.entry_id))

        
    async_add_entities(entities)

class ZeekrTravelTime(CoordinatorEntity, TimeEntity):
    def __init__(self, coordinator, prefix, day_num, day_name, entry_id):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        self.day_index = day_num
        self._local_time = None
        
        prefix_slug = prefix.lower().replace(" ", "_")
        self.entity_id = f"time.{prefix_slug}_reisplan_tijd"

        self._attr_name = f"{prefix} {day_name} Tijd"
        self._attr_unique_id = f"{entry_id}_travel_main_time"
        self._attr_icon = "mdi:clock-outline"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    @property
    def native_value(self) -> time:
        data = self.coordinator.data.get("travel", {})
        
        # 1. Haal eerst de tijd uit de API (auto)
        auto_time = None
        
        # Check scheduleList
        plans = data.get("scheduleList") or []
        for p in plans:
            if isinstance(p, dict) and p.get("startTime"):
                try:
                    h, m = map(int, p.get("startTime").split(':'))
                    auto_time = time(h, m)
                    break 
                except: continue

        # Check scheduledTime (als nog geen tijd gevonden)
        if auto_time is None:
            ts = data.get("scheduledTime")
            if ts and str(ts).isdigit() and int(ts) > 0:
                try:
                    dt = datetime.datetime.fromtimestamp(int(ts) / 1000.0)
                    auto_time = time(dt.hour, dt.minute)
                except: pass

        # 2. Logica voor lokale overschrijving:
        # Als de tijd uit de auto gelijk is aan onze lokale tijd, 
        # dan maken we de lokale tijd weer leeg zodat we de auto weer volgen.
        if self._local_time is not None and auto_time == self._local_time:
            self._local_time = None

        # Toon lokale tijd als je aan het aanpassen bent, anders de tijd uit de auto
        if self._local_time is not None:
            return self._local_time
            
        return auto_time if auto_time is not None else time(8, 0)

    async def async_set_value(self, value: time) -> None:
        self._local_time = value
        self.async_write_ha_state()

class ZeekrChargeTime(CoordinatorEntity, TimeEntity):
    def __init__(self, coordinator, entry, time_type):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        prefix = coordinator.entry.data.get('name', 'Zeekr 7X')
        self.entry = entry
        self.time_type = time_type
        self._attr_name = f"{coordinator.entry.data.get('name', 'Zeekr 7X')} Laadplan {time_type.capitalize()}tijd"
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