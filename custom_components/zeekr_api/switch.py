import asyncio
import logging
import datetime
import time as time_module
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import CONF_NAME
from .const import DOMAIN, URL_CONTROL, URL_TRAVEL, URL_CHARGE_PLAN, URL_SET_TRAVEL, URL_SET_CHARGE_PLAN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    prefix = coordinator.entry.data.get("name", "Zeekr 7X")

    # Day switches with translation keys
    day_keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    
    day_switches = []
    for i, day_key in enumerate(day_keys, 1):
        day_switches.append(ZeekrTravelDaySwitch(coordinator, prefix, i, day_key))
    
    ac_option = ZeekrTravelOptionSwitch(coordinator, prefix, "cabin_comfort", "ac")
    bw_option = ZeekrTravelOptionSwitch(coordinator, prefix, "battery_warmup", "bw")
    cycle_option = ZeekrTravelOptionSwitch(coordinator, prefix, "cycle", "cycle")

    travel_switch = ZeekrTravelPlanSwitch(coordinator, prefix, day_switches, ac_option, bw_option, cycle_option)
    hass.data[DOMAIN][f"{entry.entry_id}_travel_switch"] = travel_switch

    entities = [
        travel_switch, ac_option, bw_option, cycle_option,
        ZeekrAircoControlSwitch(coordinator, prefix),
        ZeekrChargePlanSwitch(coordinator, prefix),
        ZeekrControlSwitch(coordinator, prefix, "sentry_mode", ["sentry", "vstdModeState"], "1", "mdi:shield-lock",
            {"command": "start", "serviceId": "RSM", "setting": {"serviceParameters": [{"key": "rsm", "value": "6"}]}},
            {"command": "stop", "serviceId": "RSM", "setting": {"serviceParameters": [{"key": "rsm", "value": "6"}]}}),
        ZeekrControlSwitch(coordinator, prefix, "steering_wheel_heating", ["main", "additionalVehicleStatus", "climateStatus", "steerWhlHeatingSts"], "1", "mdi:steering", 
            {"command": "start", "serviceId": "ZAF", "setting": {"serviceParameters": [{"key": "SH.11", "value": "true"}, {"key": "SH.11.level", "value": "3"}, {"key": "SH.11.duration", "value": "8"}]}},
            {"command": "start", "serviceId": "ZAF", "setting": {"serviceParameters": [{"key": "SH.11", "value": "false"}]}}),
        ZeekrControlSwitch(coordinator, prefix, "defrost", ["main", "additionalVehicleStatus", "climateStatus", "defrost"], "1", "mdi:car-defrost-front",
            {"command": "start", "serviceId": "ZAF", "setting": {"serviceParameters": [{"key": "DF", "value": "true"}, {"key": "DF.duration", "value": "15"}]}},
            {"command": "start", "serviceId": "ZAF", "setting": {"serviceParameters": [{"key": "DF", "value": "false"}]}}),
        ZeekrControlSwitch(coordinator, prefix, "parking_comfort", ["sentry", "parkingComfortModeState"], "1", "mdi:car-seat",
            {"command": "start", "serviceId": "PCM", "setting": {"serviceParameters": [{"key": "parking_comfortable", "value": "true"}]}},
            {"command": "stop", "serviceId": "PCM", "setting": {"serviceParameters": [{"key": "parking_comfortable", "value": "false"}]}})
    ]

    entities.extend(day_switches)
    async_add_entities(entities)

class ZeekrTravelPlanSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, prefix, day_switches, ac_opt, bw_opt, cycle_opt):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "travel_plan"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_travel_plan_main"
        self._attr_icon = "mdi:calendar-clock"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)}, 
            "name": prefix, 
            "manufacturer": "Zeekr"
        }
        self._day_switches, self._ac_opt, self._bw_opt, self._cycle_opt = day_switches, ac_opt, bw_opt, cycle_opt

    @property
    def is_on(self):
        return self.coordinator.data.get("travel", {}).get("command") == "start"

    async def _send_plan(self, command):
        travel_data = self.coordinator.data.get("travel", {})
        prefix_slug = self.coordinator.entry.data.get("name", "Zeekr 7X").lower().replace(" ", "_")
        
        if command == "stop":
            payload = {
                "command": "stop",
                "timerId": str(travel_data.get("timerId", "4")),
                "bwl": str(travel_data.get("bwl", "1")),
                "ac": travel_data.get("ac", "true"),
                "bw": travel_data.get("bw", "0"),
                "scheduleList": travel_data.get("scheduleList", []),
                "scheduledTime": str(travel_data.get("scheduledTime", ""))
            }
        else:
            gen_time_state = self.hass.states.get(f"time.{prefix_slug}_travel_time")
            target_time_short = gen_time_state.state[:5] if gen_time_state else "08:00"

            if self._cycle_opt.is_on:
                schedule = []
                for sw in self._day_switches:
                    if sw.is_on:
                        schedule.append({
                            "day": str(sw.day_index),
                            "startTime": target_time_short,
                            "timerActivation": "1"
                        })
                payload = {
                    "command": "start", "timerId": "4", "bwl": "1",
                    "ac": "true" if self._ac_opt.is_on else "false",
                    "bw": "1" if self._bw_opt.is_on else "0",
                    "scheduleList": schedule, "scheduledTime": ""
                }
            else:
                now = datetime.datetime.now()
                h, m = map(int, target_time_short.split(':')[:2])
                target_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if target_dt <= now:
                    target_dt += datetime.timedelta(days=1)
                
                timestamp_ms = str(int(time_module.mktime(target_dt.timetuple()) * 1000))
                payload = {
                    "command": "start", "timerId": "", "bwl": "1",
                    "ac": "true" if self._ac_opt.is_on else "false",
                    "bw": "1" if self._bw_opt.is_on else "0",
                    "scheduleList": [], "scheduledTime": timestamp_ms 
                }

        await self.coordinator.send_command(URL_SET_TRAVEL, payload, f"Travelplan {command}")

        # Reset local overrides
        for sw in self._day_switches:
            sw._is_locally_on = None
        self._ac_opt._is_locally_on = None
        self._bw_opt._is_locally_on = None
        self._cycle_opt._is_locally_on = None

        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs):
        await self._send_plan("start")

    async def async_turn_off(self, **kwargs):
        await self._send_plan("stop")


class ZeekrAircoControlSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "ac"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_airco_sw"
        self._attr_icon = "mdi:fan"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }
        
    @property
    def is_on(self):
        return self.coordinator.data.get("main", {}).get("additionalVehicleStatus", {}).get("climateStatus", {}).get("preClimateActive") is True

    async def async_turn_on(self, **kwargs):
        name_slug = self.coordinator.entry.data.get(CONF_NAME, "Zeekr 7X").lower().replace(" ", "_")
        state = self.hass.states.get(f"climate.{name_slug}_thermostat")
        temp = str(state.attributes.get("temperature", "20.0")) if state else "20.0"
        payload = {"command": "start", "serviceId": "ZAF", "setting": {"serviceParameters": [{"key": "AC", "value": "true"}, {"key": "AC.temp", "value": temp}, {"key": "AC.duration", "value": "15"}]}}
        await self.coordinator.send_command(URL_CONTROL, payload, "Airco Aan")
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        payload = {"command": "start", "serviceId": "ZAF", "setting": {"serviceParameters": [{"key": "AC", "value": "false"}]}}
        await self.coordinator.send_command(URL_CONTROL, payload, "Airco Uit")
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()

class ZeekrControlSwitch(CoordinatorEntity, SwitchEntity):
    """Generic class for simple on/off switches like Sentry and Steering wheel."""
    def __init__(self, coordinator, prefix, translation_key, path, on_val, icon, payload_on, payload_off):
        super().__init__(coordinator)
        self.path = path
        self.on_val = on_val
        self.payload_on = payload_on
        self.payload_off = payload_off
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{translation_key}"
        self._attr_icon = icon
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }
        
    @property
    def is_on(self):
        """Get status from coordinator data based on the provided path."""
        val = self.coordinator.data
        for key in self.path:
            if isinstance(val, dict):
                val = val.get(key)
            else:
                return False
        return str(val) == str(self.on_val)

    async def async_turn_on(self, **kwargs):
        """Send the 'on' command."""
        await self.coordinator.send_command(URL_CONTROL, self.payload_on, f"{self._attr_translation_key} On")

    async def async_turn_off(self, **kwargs):
        """Send the 'off' command."""
        await self.coordinator.send_command(URL_CONTROL, self.payload_off, f"{self._attr_translation_key} Off")


class ZeekrChargePlanSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = "charge_plan"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_charge_sw"
        self._attr_icon = "mdi:battery-clock"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }
        
    @property
    def is_on(self): 
        return self.coordinator.data.get("plan", {}).get("command") == "start"
        
    async def async_turn_on(self, **kwargs):
        plan = self.coordinator.data.get("plan", {})
        start = plan.get("startTime") or "01:15"
        end = plan.get("endTime") or "06:45"
        p = {"target": 2, "endTime": end, "timerId": "2", "startTime": start, "command": "start"}
        await self.coordinator.send_command(URL_SET_CHARGE_PLAN, p, "Laadplan Aan")
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()
        
    async def async_turn_off(self, **kwargs):
        p = {"target": 2, "timerId": "2", "startTime": "01:15", "command": "stop"}
        await self.coordinator.send_command(URL_SET_CHARGE_PLAN, p, "Laadplan Uit")
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()

class ZeekrTravelDaySwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, prefix, day_num, translation_key):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        self.day_index = day_num
        
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{translation_key}"
        self._is_locally_on = None
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }
        
    @property
    def is_on(self):
        if self._is_locally_on is not None: 
            return self._is_locally_on
            
        schedules = self.coordinator.data.get("travel", {}).get("scheduleList") or []
        return any(str(p.get("day")) == str(self.day_index) for p in schedules if isinstance(p, dict))
        
    async def async_turn_on(self, **kwargs): 
        self._is_locally_on = True
        self.async_write_ha_state()
        
    async def async_turn_off(self, **kwargs): 
        self._is_locally_on = False
        self.async_write_ha_state()

class ZeekrTravelOptionSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, prefix, translation_key, key):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        self.key = key
        
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{translation_key}"
        self._is_locally_on = None
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }
        
    @property
    def is_on(self):
        if self._is_locally_on is not None: 
            return self._is_locally_on
            
        travel_data = self.coordinator.data.get("travel", {})
        if not isinstance(travel_data, dict):
            return False

        if self.key == "cycle":
            schedules = travel_data.get("scheduleList") or []
            return any(str(p.get("timerActivation")) == "1" for p in schedules if isinstance(p, dict))
            
        return str(travel_data.get(self.key)).lower() in ["true", "1"]

    async def async_turn_on(self, **kwargs): 
        self._is_locally_on = True
        self.async_write_ha_state()
        
    async def async_turn_off(self, **kwargs): 
        self._is_locally_on = False
        self.async_write_ha_state()
