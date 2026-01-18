# Zeekr API - Home Assistant Integration

A comprehensive Home Assistant integration for Zeekr vehicles with automatic token refresh functionality.

## Features

🚗 **Comprehensive Vehicle Control**
- Climate control with multiple preset modes
- Door locks and trunk control
- Charge scheduling and limits
- Travel planning with weekly schedules
- Sentry mode and car wash mode

📊 **Rich Sensor Data**
- Battery level and charging status
- Real-time GPS location tracking
- Tire pressure and temperature (all 4 wheels)
- Interior temperature
- Range and odometer
- Service intervals

🌍 **Multi-language Support**
- English 🇬🇧
- Svenska (Swedish) 🇸🇪
- Nederlands (Dutch) 🇳🇱

## Supported Entities

### Sensors (25+)
- Battery percentage
- Charging status (with states: not charging, charging, connected, charge complete)
- Charging current, voltage, and power
- Range and odometer
- Tire pressure and temperature (all 4 wheels)
- Interior temperature
- Days and distance to service
- Vehicle and engine status

### Binary Sensors (13)
- Air conditioning status
- Charging cable connected
- All doors (driver, passenger, rear left, rear right)
- Trunk and frunk
- Camping mode and car wash mode
- Washer fluid level

### Controls
- **Climate**: Full climate control with preset modes (standard, quick heat, quick cool)
- **Lock**: Central door lock
- **Cover**: Electric sunshade
- **Number**: Charge limit (50-100%)
- **Switches**: 
  - Travel plan with cabin preconditioning
  - Battery conditioning
  - Charge scheduling
  - Sentry mode
  - Steering wheel heating
  - Defrost
  - Weekly schedule (individual day toggles)

### Other
- **Buttons**: Refresh data, open trunk, update travel plan
- **Device Tracker**: GPS location
- **Time**: Charge start/end times, travel departure time

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Download the latest release
2. Copy the `zeekr_api` folder to your `custom_components` directory
3. Restart Home Assistant

## Configuration

### Getting Your Credentials

You'll need to extract your credentials from the Zeekr app using a network proxy tool like [Proxyman](https://proxyman.io/) (iOS/Mac) or similar.

1. **Install a network proxy tool** on your computer
2. **Configure your phone** to use the proxy
3. **Open the Zeekr app** and log in
4. **Find the POST request** to `/ms-user-auth/v1.0/auth/login`

In the **Response**, you'll find:
- `data.accessToken` - Your **Access Token** (remove "Bearer " prefix if present)
- `data.refreshToken` - Your **Refresh Token** (optional but recommended)


In the **Request headers**, you'll find:
- `X-VIN` - Your **VIN** (Vehicle Identification Number)

### Adding the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **"Zeekr API"**
4. Enter your credentials:
   - **Vehicle Name**: A friendly name for your vehicle
   - **VIN**: Your vehicle identification number
   - **Access Token**: The JWT token (required)

## Usage Examples

### Automations

**Start climate control before leaving**
```yaml
automation:
  - alias: "Morning Climate Control"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.zeekr_charging
        state: "on"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.zeekr_climate_control
        data:
          temperature: 21
          hvac_mode: "heat_cool"
```

**Notify when charging is complete**
```yaml
automation:
  - alias: "Charge Complete Notification"
    trigger:
      - platform: state
        entity_id: sensor.zeekr_charging_status
        to: "charge_complete"
    action:
      - service: notify.mobile_app
        data:
          title: "Zeekr"
          message: "Charging complete! Battery at {{ states('sensor.zeekr_battery') }}%"
```

**Open trunk via voice command**
```yaml
script:
  open_zeekr_trunk:
    alias: "Open Zeekr Trunk"
    sequence:
      - service: button.press
        target:
          entity_id: button.zeekr_open_trunk
```

### Lovelace Card Example

```yaml
type: entities
title: Zeekr 7X
entities:
  - entity: sensor.zeekr_battery
    name: Battery
  - entity: sensor.zeekr_range
    name: Range
  - entity: sensor.zeekr_charging_status
    name: Charging
  - entity: climate.zeekr_climate_control
    name: Climate
  - entity: lock.zeekr_door_lock
    name: Doors
  - entity: device_tracker.zeekr_location
    name: Location
```

## Troubleshooting

### "Token has expired"
- If you didn't provide a refresh token, use the "Reconfigure" option to enter a new access token
- If you did provide a refresh token, check the logs for token refresh errors

### "Platform zeekr_api.X not found"
- Make sure ALL files are copied to the `custom_components/zeekr_api/` directory
- Clear Home Assistant cache: stop HA, delete `__pycache__` folders, restart HA
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed steps

### Integration doesn't load
- Check Home Assistant logs for detailed error messages
- Verify all 16 files are present in the integration folder
- Run the verification script: `./verify_checksums.sh`

### Enable Debug Logging

Add to your `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    custom_components.zeekr_api: debug
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Adding Translations

We welcome translations for additional languages! See [translations/README.md](translations/README.md) for details.

Currently supported languages:
- English (en)
- Svenska (sv) 
- Nederlands (nl)

## Credits

- Reverse engineered from the Zeekr mobile app API
- Built with ❤️ for the Home Assistant community

## Disclaimer

This integration is not officially supported by Zeekr. Use at your own risk. The authors are not responsible for any damage to your vehicle or account.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 🐛 [Report a bug](https://github.com/yourusername/zeekr_api/issues)
- 💡 [Request a feature](https://github.com/yourusername/zeekr_api/issues)
- 💬 [Discussions](https://github.com/yourusername/zeekr_api/discussions)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

