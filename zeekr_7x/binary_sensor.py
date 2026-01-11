from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    p = coordinator.entry.data.get("name", "Zeekr 7X")
    
    entities = [
        # Status
        ZeekrBinary(coordinator, p, "Airco Actief", BinarySensorDeviceClass.RUNNING, ["main", "additionalVehicleStatus", "climateStatus", "preClimateActive"]),
        ZeekrBinary(coordinator, p, "Laadkabel", BinarySensorDeviceClass.PLUG, ["main", "additionalVehicleStatus", "electricVehicleStatus", "statusOfChargerConnection"], check_list=["1", "3"]),
        ZeekrBinary(coordinator, p, "Laden", BinarySensorDeviceClass.BATTERY_CHARGING, ["qrvs", "chargerState"], check_val="2"),
        
        # Deuren & Kofferbak
        ZeekrBinary(coordinator, p, "Frunk", BinarySensorDeviceClass.DOOR, ["main", "additionalVehicleStatus", "drivingSafetyStatus", "engineHoodOpenStatus"]),
        ZeekrBinary(coordinator, p, "Kofferbak", BinarySensorDeviceClass.DOOR, ["main", "additionalVehicleStatus", "drivingSafetyStatus", "trunkOpenStatus"]),
        ZeekrBinary(coordinator, p, "Kofferbak Slot", BinarySensorDeviceClass.LOCK, ["main", "additionalVehicleStatus", "drivingSafetyStatus", "trunkLockStatus"], invert=True),
        ZeekrBinary(coordinator, p, "Bestuurdersdeur", BinarySensorDeviceClass.DOOR, ["main", "additionalVehicleStatus", "drivingSafetyStatus", "doorOpenStatusDriver"]),
        ZeekrBinary(coordinator, p, "Passagiersdeur", BinarySensorDeviceClass.DOOR, ["main", "additionalVehicleStatus", "drivingSafetyStatus", "doorOpenStatusPassenger"]),
        ZeekrBinary(coordinator, p, "Achterdeur Bestuurder", BinarySensorDeviceClass.DOOR, ["main", "additionalVehicleStatus", "drivingSafetyStatus", "doorOpenStatusDriverRear"]),
        ZeekrBinary(coordinator, p, "Achterdeur Passagier", BinarySensorDeviceClass.DOOR, ["main", "additionalVehicleStatus", "drivingSafetyStatus", "doorOpenStatusPassengerRear"]),
        
        # Sentry & Comfort
        ZeekrBinary(coordinator, p, "Camping Modus", None, ["sentry", "campingModeState"], icon="mdi:tent"),
        ZeekrBinary(coordinator, p, "Wasstraat Modus", None, ["sentry", "washCarModeState"], icon="mdi:car-wash"),
        ZeekrBinary(coordinator, p, "Ruitenvloeistof", BinarySensorDeviceClass.PROBLEM, ["main", "maintenanceStatus", "washerFluidLevelStatus"], invert=True),
    ]
    async_add_entities(entities)

class ZeekrBinary(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, prefix, name, dev_class, path, invert=False, check_val=None, check_list=None, icon=None):
        super().__init__(coordinator)
        self.path, self.invert, self.check_val, self.check_list = path, invert, check_val, check_list
        vin = coordinator.entry.data.get('vin'); 
        self._attr_name = f"{prefix} {name}"
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{name.lower().replace(' ', '_')}"
        self._attr_device_class = dev_class
        if icon: self._attr_icon = icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, vin)},
            "name": prefix,
            "manufacturer": "Zeekr",
        }

    @property
    def is_on(self):
        val = self.coordinator.data
        for key in self.path:
            val = val.get(key) if isinstance(val, dict) else None
        
        if self.check_val: res = str(val) == str(self.check_val)
        elif self.check_list: res = str(val) in self.check_list
        else: res = str(val) not in ["None", "False", "0", "null", ""]
        
        return not res if self.invert else res