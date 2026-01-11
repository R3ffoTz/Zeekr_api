DOMAIN = "zeekr_7x"
CONF_NAME = "name"
PLATFORMS = ["sensor", "binary_sensor", "switch", "button", "climate", "cover", "number", "lock", "device_tracker", "time"]

# API Endpoints
URL_BASE = "https://eu-snc-tsp-api-gw.zeekrlife.com"
URL_CONTROL = f"{URL_BASE}/ms-remote-control/v1.0/remoteControl/control"
URL_STATUS = f"{URL_BASE}/ms-vehicle-status/api/v1.0/vehicle/status/latest?latest=false&target=new"
URL_SENTRY = f"{URL_BASE}/ms-app-bff/api/v1.0/remoteControl/getVehicleState"
URL_TRAVEL = f"{URL_BASE}/ms-charge-manage/api/v1.0/charge/getLatestTravelPlan"
URL_SET_TRAVEL = f"{URL_BASE}/ms-charge-manage/api/v1.0/charge/setTravelPlan"
URL_CHARGE_CONTROL = f"{URL_BASE}/ms-charge-manage/api/v1.0/charge/control"
URL_CHARGE_PLAN = f"{URL_BASE}/ms-charge-manage/api/v1.0/charge/getChargingPlan"
URL_SET_CHARGE_PLAN = f"{URL_BASE}/ms-charge-manage/api/v1.0/charge/setChargingPlan"
URL_LIST = f"{URL_BASE}/ms-app-bff/api/v4.0/veh/vehicle-list?needSharedCar=true"
URL_QRVS = f"{URL_BASE}/ms-vehicle-status/api/v1.0/vehicle/status/qrvs"
URL_SOC = f"{URL_BASE}/ms-charge-manage/api/v1.0/charge/getLatestSoc"