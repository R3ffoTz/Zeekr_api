import voluptuous as vol
import time as python_time
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from .const import DOMAIN

class ZeekrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            unique_id = f"zeekr_{user_input['vin'][:10]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data={
                    "name": user_input[CONF_NAME],
                    "vin": user_input["vin"],
                    "access_token": user_input["access_token"],
                    "expires_at": float(python_time.time() + 604800)
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_NAME, default="Zeekr 7X"): str,
                vol.Required("vin"): str,
                vol.Required("access_token"): str,
            })
        )

    async def async_step_reconfigure(self, user_input=None):
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                entry, 
                data={**entry.data, "access_token": user_input["access_token"], "expires_at": float(python_time.time() + 604800)}
            )
            await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({
                vol.Required("access_token"): str,
            })
        )