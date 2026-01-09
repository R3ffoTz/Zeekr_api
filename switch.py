import asyncio
import logging
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import CONF_NAME
from .const import DOMAIN, URL_CONTROL, URL_TRAVEL, URL_CHARGE_PLAN, URL_SET_TRAVEL, URL_SET_CHARGE_PLAN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    prefix = coordinator.entry.data.get("name", "Zeekr 7X")

    dagnamen = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag", "Zaterdag", "Zondag"]
    
    day_switches = []
    for i, dagnaam in enumerate(dagnamen, 1):
        day_switches.append(ZeekrTravelDaySwitch(coordinator, prefix, i, dagnaam))
    
    ac_option = ZeekrTravelOptionSwitch(coordinator, prefix, "Reisplan Cabinecomfort", "ac")
    bw_option = ZeekrTravelOptionSwitch(coordinator, prefix, "Reisplan Accubehoud", "bw")
    cycle_option = ZeekrTravelOptionSwitch(coordinator, prefix, "Reisplan Cyclus", "cycle")

    travel_switch = ZeekrTravelPlanSwitch(coordinator, prefix, day_switches, ac_option, bw_option, cycle_option)
    hass.data[DOMAIN][f"{entry.entry_id}_travel_switch"] = travel_switch

    entities = [
        travel_switch, ac_option, bw_option, cycle_option,
        ZeekrAircoControlSwitch(coordinator, prefix),
        ZeekrChargePlanSwitch(coordinator, prefix),
        ZeekrControlSwitch(coordinator, prefix, "Sentry Mode", ["sentry", "vstdModeState"], "1", "mdi:shield-lock",
            {"command": "start", "serviceId": "RSM", "setting": {"serviceParameters": [{"key": "rsm", "value": "6"}]}},
            {"command": "stop", "serviceId": "RSM", "setting": {"serviceParameters": [{"key": "rsm", "value": "6"}]}}),
        ZeekrControlSwitch(coordinator, prefix, "Stuurwielverwarming", ["main", "additionalVehicleStatus", "climateStatus", "steerWhlHeatingSts"], "1", "mdi:steering", 
            {"command": "start", "serviceId": "ZAF", "setting": {"serviceParameters": [{"key": "SH.11", "value": "true"}, {"key": "SH.11.level", "value": "3"}, {"key": "SH.11.duration", "value": "8"}]}},
            {"command": "start", "serviceId": "ZAF", "setting": {"serviceParameters": [{"key": "SH.11", "value": "false"}]}}),
        ZeekrControlSwitch(coordinator, prefix, "Ontdooien", ["main", "additionalVehicleStatus", "climateStatus", "defrost"], "1", "mdi:car-defrost-front",
            {"command": "start", "serviceId": "ZAF", "setting": {"serviceParameters": [{"key": "DF", "value": "true"}, {"key": "DF.duration", "value": "15"}]}},
            {"command": "start", "serviceId": "ZAF", "setting": {"serviceParameters": [{"key": "DF", "value": "false"}]}})
    ]

    entities.extend(day_switches)
    async_add_entities(entities)

class ZeekrTravelPlanSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, prefix, day_switches, ac_opt, bw_opt, cycle_opt):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        self._attr_name = f"{prefix} Reisplanning"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_travel_plan_main"
        self._attr_icon = "mdi:calendar-clock"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }
        self._day_switches, self._ac_opt, self._bw_opt, self._cycle_opt = day_switches, ac_opt, bw_opt, cycle_opt

    @property
    def is_on(self):
        return self.coordinator.data.get("travel", {}).get("command") == "start"

    async def _send_plan(self, command):
        travel_data = self.coordinator.data.get("travel", {})
        
        if command == "stop":
            # BELANGRIJK: Gebruik de bestaande data van de API bij een stop-commando
            payload = {
                "command": "stop",
                "timerId": travel_data.get("timerId", "4"),
                "bwl": travel_data.get("bwl", "1"),
                "ac": travel_data.get("ac", "true"),
                "bw": travel_data.get("bw", "1"),
                "scheduleList": travel_data.get("scheduleList", []),
                "scheduledTime": travel_data.get("scheduledTime", None),
                "vst": travel_data.get("vst", None),
                "vet": travel_data.get("vet", None)
            }
        else:
            schedule = []
            prefix_slug = self.coordinator.entry.data.get("name", "Zeekr 7X").lower().replace(" ", "_")
            dagnamen_en = ["maandag", "dinsdag", "woensdag", "donderdag", "vrijdag", "zaterdag", "zondag"]
            activation_mode = "2" if self._cycle_opt.is_on else "1"

            for sw in self._day_switches:
                if sw.is_on:
                    time_state = self.hass.states.get(f"time.{prefix_slug}_{dagnamen_en[sw.day_index-1]}_tijd")
                    schedule.append({
                        "day": str(sw.day_index),
                        "startTime": time_state.state[:5] if time_state else "08:00",
                        "timerActivation": activation_mode
                    })

            payload = {
                "command": "start",
                "timerId": "4",
                "bwl": "1",
                "ac": "true" if self._ac_opt.is_on else "false",
                "bw": "1" if self._bw_opt.is_on else "0",
                "scheduleList": schedule
            }

        # Gebruik de centralisereerde coordinator send_command (die wacht al 2s + refresh)
        await self.coordinator.send_command(URL_SET_TRAVEL, payload, f"Travelplan {command}")
        for sw in self._day_switches + [self._ac_opt, self._bw_opt, self._cycle_opt]:
            sw._is_locally_on = None

    async def async_turn_on(self, **kwargs): await self._send_plan("start")
    async def async_turn_off(self, **kwargs): await self._send_plan("stop")

class ZeekrAircoControlSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin')
        self._attr_name = f"{prefix} Airco"
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
        state = self.hass.states.get(f"climate.{name_slug}_thermostaat")
        temp = str(state.attributes.get("temperature", "20.0")) if state else "20.0"
        payload = {"command": "start", "serviceId": "ZAF", "setting": {"serviceParameters": [{"key": "AC", "value": "true"}, {"key": "AC.temp", "value": temp}, {"key": "AC.duration", "value": "15"}]}}
        await self.coordinator.send_command(URL_CONTROL, payload, "Airco Aan")
        await asyncio.sleep(2); await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        payload = {"command": "start", "serviceId": "ZAF", "setting": {"serviceParameters": [{"key": "AC", "value": "false"}]}}
        await self.coordinator.send_command(URL_CONTROL, payload, "Airco Uit")
        await asyncio.sleep(2); await self.coordinator.async_request_refresh()

class ZeekrControlSwitch(CoordinatorEntity, SwitchEntity):
    """Generieke klasse voor simpele aan/uit switches zoals Sentry en Stuurwiel."""
    def __init__(self, coordinator, prefix, name, path, on_val, icon, payload_on, payload_off):
        super().__init__(coordinator)
        self.path = path
        self.on_val = on_val
        self.payload_on = payload_on
        self.payload_off = payload_off
        vin = coordinator.entry.data.get('vin')
        self._attr_name = f"{prefix} {name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{name.lower().replace(' ', '_')}"
        self._attr_icon = icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }
    @property
    def is_on(self):
        """Haal de status op uit de coordinator data op basis van het opgegeven pad."""
        val = self.coordinator.data
        # We wandelen door het JSON pad (bijv. ["sentry", "vstdModeState"])
        for key in self.path:
            if isinstance(val, dict):
                val = val.get(key)
            else:
                return False
        return str(val) == str(self.on_val)

    async def async_turn_on(self, **kwargs):
        """Stuur het 'aan' commando."""
        # Gebruik URL_CONTROL uit je const.py
        await self.coordinator.send_command(URL_CONTROL, self.payload_on, f"{self._attr_name} Aan")

    async def async_turn_off(self, **kwargs):
        """Stuur het 'uit' commando."""
        await self.coordinator.send_command(URL_CONTROL, self.payload_off, f"{self._attr_name} Uit")

# Klassieke switches (Defrost, Sentry, Steer, TravelDay, TravelOption, ChargePlan)


class ZeekrChargePlanSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get('vin'); 
        self._attr_name = f"{prefix} Laadplan Actief"; self._attr_unique_id = f"{coordinator.entry.entry_id}_charge_sw"; 
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }
        self._attr_icon = "mdi:battery-clock"
    @property
    def is_on(self): return self.coordinator.data.get("plan", {}).get("command") == "start"
    async def async_turn_on(self, **kwargs):
        plan = self.coordinator.data.get("plan", {}); start = plan.get("startTime") or "01:15"; end = plan.get("endTime") or "06:45"
        p = {"target": 2, "endTime": end, "timerId": "2", "startTime": start, "command": "start"}
        await self.coordinator.send_command(URL_SET_CHARGE_PLAN, p, "Laadplan Aan"); await asyncio.sleep(2); await self.coordinator.async_request_refresh()
    async def async_turn_off(self, **kwargs):
        p = {"target": 2, "timerId": "2", "startTime": "01:15", "command": "stop"}
        await self.coordinator.send_command(URL_SET_CHARGE_PLAN, p, "Laadplan Uit"); await asyncio.sleep(2); await self.coordinator.async_request_refresh()

class ZeekrTravelDaySwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, prefix, day_num, day_name):
        super().__init__(coordinator); vin = coordinator.entry.data.get('vin'); self.day_index = day_num; self._attr_name = f"{prefix} {day_name} Actief"; self._attr_unique_id = f"{coordinator.entry.entry_id}_day_{day_num}"; self._is_locally_on = None
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }
    @property
    def is_on(self):
        if self._is_locally_on is not None: return self._is_locally_on
        return any(str(p.get("day")) == str(self.day_index) for p in self.coordinator.data.get("travel", {}).get("scheduleList", []))
    async def async_turn_on(self, **kwargs): self._is_locally_on = True; self.async_write_ha_state()
    async def async_turn_off(self, **kwargs): self._is_locally_on = False; self.async_write_ha_state()

class ZeekrTravelOptionSwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, prefix, name, key):
        super().__init__(coordinator); vin = coordinator.entry.data.get('vin'); self.key = key; self._attr_name = f"{prefix} {name}"; self._attr_unique_id = f"{coordinator.entry.entry_id}_opt_{key}"; self._is_locally_on = None
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }
    @property
    def is_on(self):
        if self._is_locally_on is not None: return self._is_locally_on
        if self.key == "cycle": return any(str(p.get("timerActivation")) == "2" for p in self.coordinator.data.get("travel", {}).get("scheduleList", []))
        return str(self.coordinator.data.get("travel", {}).get(self.key)).lower() in ["true", "1"]
    async def async_turn_on(self, **kwargs): self._is_locally_on = True; self.async_write_ha_state()
    async def async_turn_off(self, **kwargs): self._is_locally_on = False; self.async_write_ha_state()