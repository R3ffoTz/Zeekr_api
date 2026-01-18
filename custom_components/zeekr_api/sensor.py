from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTemperature, UnitOfPressure
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    prefix = coordinator.entry.data.get("name", "Zeekr 7X")
    
    sensor_definitions = [
        # --- Vehicle Identification ---
        ("software_version", ["info", "displayOSVersion"], None, "mdi:car-info", EntityCategory.DIAGNOSTIC),
        ("license_plate", ["info", "plateNo"], None, "mdi:card-account-details", None),
        ("vin", ["info", "vin"], None, "mdi:car-info", EntityCategory.DIAGNOSTIC),
        
        # --- Battery & Charging ---
        ("battery_percentage", ["main", "additionalVehicleStatus", "electricVehicleStatus", "chargeLevel"], PERCENTAGE, SensorDeviceClass.BATTERY, None),
        ("charging_status", ["qrvs", "chargerState"], None, None, None),
        ("charging_current", ["qrvs", "chargeCurrent"], "A", "mdi:current-ac", None),
        ("charging_voltage", ["qrvs", "chargeVoltage"], "V", "mdi:flash", None),
        ("charging_power", ["qrvs", "chargePower"], "kW", SensorDeviceClass.POWER, None),
        ("charging_time_minutes", ["main", "additionalVehicleStatus", "electricVehicleStatus", "timeToFullyCharged"], "min", None, None),
        ("range", ["main", "additionalVehicleStatus", "electricVehicleStatus", "distanceToEmptyOnBatteryOnly"], "km", "mdi:map-marker-distance", None),
        
        # --- Status & Drive ---
        ("vehicle_status", ["main", "basicVehicleStatus", "usageMode"], None, "mdi:car-connected", None),
        ("engine_status", ["main", "basicVehicleStatus", "engineStatus"], None, "mdi:car", None),
        
        # --- Charge Planning ---
        ("scheduled_charge_time", ["plan", "startTime"], None, "mdi:clock-outline", None),
        
        # --- Tires (Pressure & Temperature) ---
        ("tire_pressure_fl", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreStatusDriver"], "bar", SensorDeviceClass.PRESSURE, None),
        ("tire_pressure_fr", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreStatusPassenger"], "bar", SensorDeviceClass.PRESSURE, None),
        ("tire_pressure_rl", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreStatusDriverRear"], "bar", SensorDeviceClass.PRESSURE, None),
        ("tire_pressure_rr", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreStatusPassengerRear"], "bar", SensorDeviceClass.PRESSURE, None),
        ("tire_temp_fl", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreTempDriver"], "Â°C", SensorDeviceClass.TEMPERATURE, None),
        ("tire_temp_fr", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreTempPassenger"], "Â°C", SensorDeviceClass.TEMPERATURE, None),
        ("tire_temp_rl", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreTempDriverRear"], "Â°C", SensorDeviceClass.TEMPERATURE, None),
        ("tire_temp_rr", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreTempPassengerRear"], "Â°C", SensorDeviceClass.TEMPERATURE, None),
        
        # --- Maintenance & Status ---
        ("odometer", ["main", "additionalVehicleStatus", "maintenanceStatus", "odometer"], "km", "mdi:counter", None),
        ("distance_to_service", ["main", "additionalVehicleStatus","maintenanceStatus", "distanceToService"], "km", SensorDeviceClass.DISTANCE, None),
        ("days_to_service", ["main", "additionalVehicleStatus","maintenanceStatus", "daysToService"], "d", None, None),
        ("interior_temp", ["main", "additionalVehicleStatus", "climateStatus", "interiorTemp"], "Â°C", SensorDeviceClass.TEMPERATURE, None),
        
        # --- Trip Computer (Trip 2 Related) ---
        ("trip_2_distance", ["main", "additionalVehicleStatus", "runningStatus", "tripMeter2"], "km", "mdi:map-marker-distance", None),
        ("trip_2_avg_speed", ["main", "additionalVehicleStatus", "runningStatus", "avgSpeed"], "km/h", "mdi:speedometer", None),
        ("trip_2_avg_consumption", ["main", "additionalVehicleStatus", "electricVehicleStatus", "averPowerConsumption"], "kWh/100km", "mdi:lightning-bolt", None),
    ]
    
    entities = [ZeekrSensor(coordinator, prefix, *s) for s in sensor_definitions]
    
    entities.append(ZeekrChargingTimeFormattedSensor(coordinator, prefix))
    
    async_add_entities(entities)

class ZeekrSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, prefix, translation_key, path, unit, dev_class_or_icon, category):
        super().__init__(coordinator)
        self.path = path
        self._translation_key = translation_key
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{translation_key}"
        self._attr_native_unit_of_measurement = unit
        
        if category:
            self._attr_entity_category = category

        vin = coordinator.entry.data.get("vin")
        info = coordinator.data.get("info", {})
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
            "model": info.get("vehicleModelName", "7X"),
            "sw_version": info.get("softwareVersion"),
        }
        if isinstance(dev_class_or_icon, SensorDeviceClass):
            self._attr_device_class = dev_class_or_icon
        else:
            self._attr_icon = dev_class_or_icon
            
        if unit is not None:
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        data = self.coordinator.data
        val = data
        for key in self.path:
            if isinstance(val, dict):
                val = val.get(key)
            else:
                val = None
                break
        
        if val is None:
            return None

        # --- CONVERSIONS ---
        
        # A. Tire Pressure (Always to number for bar)
        if "tire_pressure" in self._translation_key:
            try:
                return round(float(val) / 100, 2)
            except: return val

        # B. Battery & Limit (Always to number)
        if "charge_limit" in self._translation_key:
            try:
                num = float(val)
                return num / 10 if num > 100 else num
            except: return val

        # C. Charging Status - return key for translation
        if "charging_status" in self._translation_key:
            status_map = {
                "0": "not_charging",
                "2": "charging",
                "3": "connected",
                "4": "charge_complete"
            }
            return status_map.get(str(val).strip(), val)

        # D. Trip 2 Distance - convert meters to km
        if "trip_2_distance" in self._translation_key:
            try:
                return round(float(val) / 1000, 1)  # meters to km with 1 decimal
            except (ValueError, TypeError): return val

        # E. Round kilometers
        if self._attr_native_unit_of_measurement == "km":
            try:
                return int(float(val))
            except (ValueError, TypeError): return val

        # E. Engine Status - return key for translation
        if "engine_status" in self._translation_key:
            status_map = {
                "engine-off": "parked",
                "engine-running": "driving",
                "ready": "ready",
                "charging": "charging"
            }
            return status_map.get(str(val).strip().lower(), val)

        # F. Vehicle Status - return key for translation
        if "vehicle_status" in self._translation_key:
            status_map = {
                "0": "deep_sleep",
                "1": "parked",
                "2": "unlocked",
                "3": "system_active",
                "4": "ready_to_go",
                "13": "active",
            }
            return status_map.get(str(val).strip(), val)
            
        return val

class ZeekrChargingTimeFormattedSensor(CoordinatorEntity, SensorEntity):
    """Special sensor for nice display of charging time."""
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get("vin")
        info = coordinator.data.get("main", {}).get("vehicleBasicInfo", {})
        self.path = ["main", "additionalVehicleStatus", "electricVehicleStatus", "timeToFullyCharged"]
        
        self._attr_translation_key = "charging_time_remaining"
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_charging_time_formatted"
        self._attr_icon = "mdi:timer-sand"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
            "model": info.get("vehicleModelName", "7X"),
            "sw_version": info.get("softwareVersion"),
        }
        
    @property
    def native_value(self):
        val = self.coordinator.data
        for key in self.path:
            if isinstance(val, dict):
                val = val.get(key)
            else:
                return None
        
        try:
            minutes = int(val)
            if minutes >= 2047 or minutes <= 0:
                return "Not charging"
            
            hours, mins = divmod(minutes, 60)
            if hours > 0:
                return f"{hours}h {mins}m"
            return f"{mins}m"
        except (ValueError, TypeError):
            return "Unknown"
