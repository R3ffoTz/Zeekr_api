from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTemperature, UnitOfPressure
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    prefix = coordinator.entry.data.get("name", "Zeekr 7X")
    
    sensor_definitions = [
        # --- Voertuig Identificatie ---
        ("Software Versie", ["info", "displayOSVersion"], None, "mdi:car-info"),
        ("Kenteken", ["info", "plateNo"], None, "mdi:card-account-details"),
        ("Vin", ["info", "vin"], None, "mdi:car-info"),
        
        # --- Batterij & Laden ---
        ("Accu Percentage", ["main", "additionalVehicleStatus", "electricVehicleStatus", "chargeLevel"], PERCENTAGE, SensorDeviceClass.BATTERY),
        ("Laadstatus", ["qrvs", "chargerState"], None, None),
        ("Laadstroom", ["qrvs", "chargeCurrent"], "A", "mdi:current-ac"),
        ("Laadspanning", ["qrvs", "chargeVoltage"], "V", "mdi:flash"),
        ("Laadvermogen", ["qrvs", "chargePower"], "kW", SensorDeviceClass.POWER),
        ("Laadtijd Minuten", ["main", "additionalVehicleStatus", "electricVehicleStatus", "timeToFullyCharged"], "min", None),
        ("Actieradius", ["main", "additionalVehicleStatus", "electricVehicleStatus", "distanceToEmptyOnBatteryOnly"], "km", SensorDeviceClass.DISTANCE),

        # --- Laadplanning (Direct uit de API) ---
        ("Geplande Laadtijd", ["plan", "startTime"], None, "mdi:clock-outline"),
        
        # --- Banden (Spanning & Temperatuur) ---
        ("Bandenspanning LV", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreStatusDriver"], "bar", SensorDeviceClass.PRESSURE),
        ("Bandenspanning RV", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreStatusPassenger"], "bar", SensorDeviceClass.PRESSURE),
        ("Bandenspanning LA", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreStatusDriverRear"], "bar", SensorDeviceClass.PRESSURE),
        ("Bandenspanning RA", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreStatusPassengerRear"], "bar", SensorDeviceClass.PRESSURE),
        ("Bandentemperatuur LV", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreTempDriver"], "°C", SensorDeviceClass.TEMPERATURE),
        ("Bandentemperatuur RV", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreTempPassenger"], "°C", SensorDeviceClass.TEMPERATURE),
        ("Bandentemperatuur LA", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreTempDriverRear"], "°C", SensorDeviceClass.TEMPERATURE),
        ("Bandentemperatuur RA", ["main", "additionalVehicleStatus","maintenanceStatus", "tyreTempPassengerRear"], "°C", SensorDeviceClass.TEMPERATURE),
        
        # --- Onderhoud & Status ---
        ("Kilometerstand", ["main", "additionalVehicleStatus", "maintenanceStatus", "odometer"], "km", "mdi:counter"),
        ("Afstand tot Onderhoud", ["main", "additionalVehicleStatus","maintenanceStatus", "distanceToService"], "km", SensorDeviceClass.DISTANCE),
        ("Dagen tot Onderhoud", ["main", "additionalVehicleStatus","maintenanceStatus", "daysToService"], "dagen", None),
        ("Binnen Temperatuur", ["main", "additionalVehicleStatus", "climateStatus", "interiorTemp"], "°C", SensorDeviceClass.TEMPERATURE),
    ]
    
    entities = [ZeekrSensor(coordinator, prefix, *s) for s in sensor_definitions]
    
    # Voeg de extra 'Nette' laadtijd sensor toe (gebaseerd op hetzelfde pad als de minuten)
    entities.append(ZeekrChargingTimeFormattedSensor(coordinator, prefix))
    
    async_add_entities(entities)

class ZeekrSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, prefix, name, path, unit, dev_class_or_icon):
        super().__init__(coordinator)
        self.path = path
        self._raw_name = name
        self._attr_name = f"{prefix} {name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{name.lower().replace(' ', '_')}"
        self._attr_native_unit_of_measurement = unit

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

        # --- CONVERSIES ---
        
        # A. Bandenspanning (Altijd naar getal voor bar)
        if "Bandenspanning" in self._raw_name:
            try:
                return round(float(val) / 100, 2)
            except: return val

        # B. Accu & Limiet (Altijd naar getal)
        if any(x in self._raw_name for x in ["Laadlimiet"]):
            try:
                num = float(val)
                return num / 10 if num > 100 else num
            except: return val

        # C. Laadstatus
        if "Laadstatus" in self._raw_name:
            mapping = {"0": "Niet verbonden", "2": "Aan het laden", "3": "Verbonden", "4": "Laden voltooid"}
            return mapping.get(str(val).strip(), f"Status {val}")

        # D. Kilometers afronden
        if any(unit in str(self._attr_native_unit_of_measurement) for unit in ["km"]):
            try:
                return int(float(val))
            except:
                return val

        return val

class ZeekrChargingTimeFormattedSensor(CoordinatorEntity, SensorEntity):
    """Speciale sensor voor nette weergave van laadtijd."""
    def __init__(self, coordinator, prefix):
        super().__init__(coordinator)
        vin = coordinator.entry.data.get("vin")
        info = coordinator.data.get("main", {}).get("vehicleBasicInfo", {})
        self.path = ["main", "additionalVehicleStatus", "electricVehicleStatus", "timeToFullyCharged"]
        self._attr_name = f"{prefix} Laadtijd Resterend"
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
                return "Niet aan het laden"
            
            hours, mins = divmod(minutes, 60)
            if hours > 0:
                return f"{hours}u {mins}m"
            return f"{mins}m"
        except (ValueError, TypeError):
            return "Onbekend"