from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    p = coordinator.entry.data.get("name", "Zeekr 7X")
    
    entities = [
        # Status
        ZeekrBinary(coordinator, p, "ac_active", BinarySensorDeviceClass.RUNNING, ["main", "additionalVehicleStatus", "climateStatus", "preClimateActive"]),
        ZeekrBinary(coordinator, p, "charging_cable", BinarySensorDeviceClass.PLUG, ["main", "additionalVehicleStatus", "electricVehicleStatus", "statusOfChargerConnection"], check_list=["1", "3"]),
        ZeekrBinary(coordinator, p, "charging", BinarySensorDeviceClass.BATTERY_CHARGING, ["qrvs", "chargerState"], check_val="2"),
        
        # Deuren & Kofferbak
        ZeekrBinary(coordinator, p, "frunk", BinarySensorDeviceClass.DOOR, ["main", "additionalVehicleStatus", "drivingSafetyStatus", "engineHoodOpenStatus"]),
        ZeekrBinary(coordinator, p, "trunk", BinarySensorDeviceClass.DOOR, ["main", "additionalVehicleStatus", "drivingSafetyStatus", "trunkOpenStatus"]),
        ZeekrBinary(coordinator, p, "trunk_lock", BinarySensorDeviceClass.LOCK, ["main", "additionalVehicleStatus", "drivingSafetyStatus", "trunkLockStatus"], invert=True),
        ZeekrBinary(coordinator, p, "driver_door", BinarySensorDeviceClass.DOOR, ["main", "additionalVehicleStatus", "drivingSafetyStatus", "doorOpenStatusDriver"]),
        ZeekrBinary(coordinator, p, "passenger_door", BinarySensorDeviceClass.DOOR, ["main", "additionalVehicleStatus", "drivingSafetyStatus", "doorOpenStatusPassenger"]),
        ZeekrBinary(coordinator, p, "rear_driver_door", BinarySensorDeviceClass.DOOR, ["main", "additionalVehicleStatus", "drivingSafetyStatus", "doorOpenStatusDriverRear"]),
        ZeekrBinary(coordinator, p, "rear_passenger_door", BinarySensorDeviceClass.DOOR, ["main", "additionalVehicleStatus", "drivingSafetyStatus", "doorOpenStatusPassengerRear"]),
        
        # Sentry & Comfort
        ZeekrBinary(coordinator, p, "camping_mode", None, ["sentry", "campingModeState"], icon="mdi:tent"),
        ZeekrBinary(coordinator, p, "car_wash_mode", None, ["sentry", "washCarModeState"], icon="mdi:car-wash"),
        ZeekrBinary(coordinator, p, "washer_fluid", BinarySensorDeviceClass.PROBLEM, ["main", "maintenanceStatus", "washerFluidLevelStatus"], invert=True),
    ]
    async_add_entities(entities)

class ZeekrBinary(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, prefix, translation_key, dev_class, path, invert=False, check_val=None, check_list=None, icon=None):
        super().__init__(coordinator)
        self.path, self.invert, self.check_val, self.check_list = path, invert, check_val, check_list
        vin = coordinator.entry.data.get('vin')
        
        self._attr_translation_key = translation_key
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{translation_key}"
        self._attr_device_class = dev_class
        if icon: 
            self._attr_icon = icon
        
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
        
        if self.check_val: 
            res = str(val) == str(self.check_val)
        elif self.check_list: 
            res = str(val) in self.check_list
        else: 
            res = str(val) not in ["None", "False", "0", "null", ""]
        
        return not res if self.invert else res
