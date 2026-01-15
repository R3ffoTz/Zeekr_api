import voluptuous as vol
import time as python_time
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from .const import DOMAIN

class ZeekrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Hantera initial konfiguration."""
        errors = {}
        
        if user_input is not None:
            unique_id = f"zeekr_{user_input['vin'][:10]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # Generera ett device_id
            import uuid
            device_id = str(uuid.uuid4())
            
            # Beräkna expires_at (7 dagar från nu)
            expires_at = float(python_time.time() + 604800)

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    "name": user_input[CONF_NAME],
                    "vin": user_input["vin"],
                    "access_token": user_input["access_token"],
                    "refresh_token": user_input.get("refresh_token", ""),
                    "identifier": user_input.get("identifier", ""),
                    "expires_at": expires_at,
                    "refresh_expires_at": float(python_time.time() + 2592000),  # 30 dagar
                    "device_id": device_id
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default="Zeekr API"): str,
                vol.Required("vin"): str,
                vol.Required("access_token"): str,
                vol.Optional("refresh_token", default=""): str,
                vol.Optional("identifier", default=""): str,
            }),
            errors=errors
        )

    async def async_step_reconfigure(self, user_input=None):
        """Hantera omkonfigurering av tokens."""
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        
        if user_input is not None:
            # Behåll gamla värden och uppdatera endast det som ändrats
            new_data = {**entry.data}
            
            # Uppdatera bara fält som faktiskt har värden
            if user_input.get("access_token"):
                new_data["access_token"] = user_input["access_token"]
                new_data["expires_at"] = float(python_time.time() + 604800)
            
            if user_input.get("refresh_token"):
                new_data["refresh_token"] = user_input["refresh_token"]
                new_data["refresh_expires_at"] = float(python_time.time() + 2592000)
            
            if user_input.get("identifier"):
                new_data["identifier"] = user_input["identifier"]
            
            self.hass.config_entries.async_update_entry(entry, data=new_data)
            await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Optional("access_token"): str,
                vol.Optional("refresh_token"): str,
                vol.Optional("identifier"): str,
            })
        )
