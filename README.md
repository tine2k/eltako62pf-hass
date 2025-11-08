# Eltako ESR62PF-IP Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/tine2k/eltako62pf-hass.svg)](https://github.com/tine2k/eltako62pf-hass/releases)
[![License](https://img.shields.io/github/license/tine2k/eltako62pf-hass.svg)](LICENSE)

Custom Home Assistant integration for controlling Eltako ESR62PF-IP relay devices.

## Overview

The Eltako ESR62PF-IP is a network-connected relay control device that provides remote switching capabilities. This integration allows Home Assistant users to control relays, monitor device status, and automate operations through the Home Assistant ecosystem.

## Features

- **Easy Configuration**: UI-based config flow for simple device setup
- **Automatic Device Discovery**: Automatically discovers all relays connected to your Eltako device
- **Switch Platform**: Control relays as standard Home Assistant switches
- **Optimistic Updates**: Immediate UI response for relay operations
- **Optional Polling**: Configurable state synchronization with the device
- **Secure Authentication**: Support for self-signed SSL certificates
- **Token Management**: Automatic API key refresh and token handling
- **Error Recovery**: Robust error handling with automatic reconnection

## Requirements

- Home Assistant 2024.1.0 or newer
- Eltako ESR62PF-IP device with network connectivity
- Device PoP (Proof of Possession) credential

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL: `https://github.com/tine2k/eltako62pf-hass`
5. Select category: "Integration"
6. Click "Add"
7. Search for "Eltako ESR62PF-IP" in HACS
8. Click "Download"
9. Restart Home Assistant

### Manual Installation

1. Download the latest release from the [releases page](https://github.com/tine2k/eltako62pf-hass/releases)
2. Extract the files
3. Copy the `custom_components/eltako_esr62pf` folder to your Home Assistant `custom_components` directory
4. Restart Home Assistant

## Configuration

### Adding the Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Eltako ESR62PF-IP"
4. Enter the required information:
   - **IP Address**: The IP address of your Eltako device
   - **Port**: The port number (default: 443)
   - **PoP**: Your device's Proof of Possession credential
5. Click **Submit**

The integration will automatically discover all relays connected to your device and create switch entities for them.

### Configuration Options

After setup, you can configure additional options:

1. Go to **Settings** → **Devices & Services**
2. Find the "Eltako ESR62PF-IP" integration
3. Click **Configure**
4. Available options:
   - **Polling Interval**: Set how often to poll the device for state updates (default: disabled)
     - Set to 0 to disable polling (recommended)
     - Minimum: 10 seconds
     - Recommended: 30-60 seconds if enabled

## Usage

### Controlling Relays

Once configured, relays appear as switch entities in Home Assistant:

```yaml
# Example: Turn on a relay
service: switch.turn_on
target:
  entity_id: switch.eltako_relay_1

# Example: Turn off a relay
service: switch.turn_off
target:
  entity_id: switch.eltako_relay_2

# Example: Toggle a relay
service: switch.toggle
target:
  entity_id: switch.eltako_relay_3
```

### Automation Example

```yaml
automation:
  - alias: "Turn on lights at sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.eltako_relay_1
```

## Entity Naming

Entities are named based on the device name and relay number:
- Format: `switch.eltako_{device_name}_{relay_number}`
- Example: `switch.eltako_living_room_1`

## Advanced Examples

### Time-Based Automation

```yaml
automation:
  - alias: "Office lights schedule"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.eltako_office_1

  - alias: "Office lights off"
    trigger:
      - platform: time
        at: "18:00:00"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.eltako_office_1
```

### Sensor-Triggered Automation

```yaml
automation:
  - alias: "Motion activated lighting"
    trigger:
      - platform: state
        entity_id: binary_sensor.hallway_motion
        to: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.eltako_hallway_1
      - delay:
          minutes: 5
      - service: switch.turn_off
        target:
          entity_id: switch.eltako_hallway_1
```

### Scene Integration

```yaml
scene:
  - name: "Movie Time"
    entities:
      switch.eltako_living_room_1: off
      switch.eltako_living_room_2: on
      switch.eltako_hallway_1: off
```

### Script Example

```yaml
script:
  evening_routine:
    sequence:
      - service: switch.turn_on
        target:
          entity_id:
            - switch.eltako_living_room_1
            - switch.eltako_kitchen_1
      - delay:
          seconds: 2
      - service: switch.turn_off
        target:
          entity_id: switch.eltako_bedroom_1
```

### Template Example

```yaml
automation:
  - alias: "Conditional relay control"
    trigger:
      - platform: numeric_state
        entity_id: sensor.outdoor_temperature
        below: 15
    condition:
      - condition: time
        after: "18:00:00"
        before: "23:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.eltako_heater_1
```

## API Reference

This integration communicates with the Eltako ESR62PF-IP device using its REST API. Below are the main endpoints used:

### Authentication Endpoint

**Login and obtain API key:**

```http
POST https://{device_ip}:443/api/v0/login
Content-Type: application/json

{
  "user": "admin",
  "password": "{your_pop_credential}"
}
```

**Response:**
```json
{
  "apiKey": "xxxxx-xxxxx-xxxxx-xxxxx"
}
```

**Notes:**
- API keys are valid for 15 minutes
- The integration automatically refreshes tokens before expiry
- Username is always "admin" (hardcoded)

### Device Discovery Endpoint

**Get list of all connected devices:**

```http
GET https://{device_ip}:443/api/v0/devices
Authorization: {apiKey}
```

**Response:**
```json
[
  {
    "deviceGuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "name": "Relay 1",
    "type": "relay",
    ...
  },
  ...
]
```

### Relay Control Endpoint

**Control a specific relay:**

```http
PUT https://{device_ip}:443/api/v0/devices/{device_guid}/functions/relay
Authorization: {apiKey}
Content-Type: application/json

{
  "type": "enumeration",
  "identifier": "relay",
  "value": "on"
}
```

**Parameters:**
- `value`: Either `"on"` or `"off"`
- `device_guid`: The unique identifier from the devices list

**Response:**
- HTTP 200 on success
- HTTP 401 if API key is expired (integration will refresh and retry)
- HTTP 404 if device GUID is invalid

## Known Limitations

### Authentication and Security
- **API Token Expiry**: API tokens are valid for 15 minutes and are automatically refreshed by the integration
- **Self-Signed SSL Certificates**: The device uses self-signed SSL certificates (this is expected and fully supported)
- **Fixed Username**: The username is hardcoded as "admin" and cannot be changed
- **HTTPS Only**: All communication must be over HTTPS (port 443 by default)

### State Management
- **Polling Disabled by Default**: State polling is disabled by default to reduce API calls and improve performance
  - Enable polling only if you need to track external relay state changes
  - Recommended interval: 30-60 seconds when enabled
  - Minimum interval: 10 seconds (enforced)
- **Optimistic Updates**: By default, the integration uses optimistic updates (UI updates immediately without waiting for device confirmation)
- **No Webhook Support**: The device doesn't support webhooks or push notifications; state updates rely on polling or optimistic updates

### Performance Constraints
- **Response Time**: Maximum response time is approximately 500ms for relay operations under normal network conditions
- **Concurrent Operations**: While the integration handles concurrent requests, excessive simultaneous operations may cause delays
- **Network Dependency**: The integration requires continuous network connectivity; offline operation is not supported

### Device and Integration Limitations
- **Single Device Instance**: Each integration entry supports one Eltako ESR62PF-IP device
  - To control multiple devices, add multiple integration instances
- **Relay Discovery**: Relays are discovered during initial setup; dynamic relay addition requires integration reload
- **No Energy Monitoring**: The integration does not support energy monitoring or power consumption tracking
- **No Pulse/Timer Functions**: Advanced features like pulse control or timer functions are not currently implemented

### Compatibility
- **Home Assistant Version**: Requires Home Assistant 2024.1.0 or newer
- **Python Version**: Requires Python 3.11 or later
- **Network Requirements**: IPv4 networking only; IPv6 is not supported
- **Firmware Compatibility**: Tested with current firmware versions; older firmware may have compatibility issues

### Data and State Persistence
- **State Persistence**: Entity states persist across Home Assistant restarts
- **No Historical Data**: The integration doesn't store historical state data beyond what Home Assistant core provides
- **Configuration Changes**: Changes to device configuration (IP, PoP) require removing and re-adding the integration

For planned enhancements and future features, see the [project roadmap](https://github.com/tine2k/eltako62pf-hass/issues) on GitHub.

## Troubleshooting

### Connection Issues

If you experience connection issues:

1. **Verify Network Settings**
   - Confirm the IP address is correct
   - Verify the port (default: 443)
   - Ensure the device is reachable: `ping {device_ip}`
   - Check firewall rules aren't blocking port 443

2. **Check Device Status**
   - Verify the Eltako device is powered on
   - Ensure network cable is connected
   - Check device LED indicators for status

3. **Review Error Messages**
   - Check Home Assistant logs for detailed errors
   - Common errors:
     - `cannot_connect`: Network unreachable or device offline
     - `timeout`: Device not responding (check network latency)
     - `unknown`: Unexpected error (check logs)

### SSL Certificate Errors

The Eltako ESR62PF-IP uses **self-signed SSL certificates** by default. This is expected behavior:

- The integration automatically handles self-signed certificates
- You may see SSL warnings in logs - these are normal
- The integration uses `verify_ssl=False` internally for this device
- No action required from users

If you experience SSL-related connection failures:
1. Ensure you're using `https://` in the IP address
2. Check that port 443 is accessible
3. Verify the device firmware is up to date

### Authentication Errors

**Invalid PoP Credential:**
```
Error: invalid_auth
```
**Solution:**
- Double-check your PoP (Proof of Possession) credential
- The PoP is case-sensitive
- Try removing and re-adding the integration with the correct PoP

**Token Expiry Issues:**
- API tokens are valid for 15 minutes
- The integration automatically refreshes tokens
- If you see repeated authentication errors, check the logs for token refresh failures

### Polling Configuration Issues

**When to Enable Polling:**
- Polling is **disabled by default** for best performance
- Enable polling only if you need state synchronization when relays are controlled externally (outside Home Assistant)
- Example: Physical switches or another control system

**Recommended Settings:**
- **Disabled (default):** Best for most users - relies on optimistic updates
- **30-60 seconds:** Good balance if polling needed
- **Minimum:** 10 seconds (enforced by integration)

**If Polling Causes Issues:**
1. Go to Settings → Devices & Services
2. Find Eltako ESR62PF-IP integration
3. Click Configure
4. Set polling interval to 0 to disable

### State Synchronization Problems

**States Not Updating:**
- With polling disabled (default), states update optimistically (immediately when you control them)
- External changes (physical switches) won't be reflected unless polling is enabled
- This is expected behavior - enable polling if you need external state tracking

**Delayed State Updates:**
- Check your polling interval setting
- Increase interval to reduce API load
- Verify network latency isn't causing delays

### Device Discovery Failures

**No Relays Found:**
1. Verify the device is properly configured
2. Check that relays are connected to the Eltako device
3. Remove and re-add the integration
4. Check logs for API errors during device discovery

**Missing Relays:**
- Some relays may not appear if they're not configured on the device
- Verify relay configuration in the Eltako device settings
- Reload the integration to re-scan for devices

### Performance Issues

**Slow Response Times:**
- Normal response time: < 500ms
- If slower:
  - Check network latency: `ping {device_ip}`
  - Verify device isn't overloaded with requests
  - Reduce polling frequency if enabled
  - Check for network congestion

**Integration Using Too Much Resources:**
- Disable polling if not needed
- Increase polling interval (e.g., 60 seconds instead of 10)
- Check for automation loops (automations triggering each other)

### Log Collection and Debugging

**Enable Debug Logging:**

Add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.eltako_esr62pf: debug
```

Then restart Home Assistant.

**View Logs:**
1. Go to Settings → System → Logs
2. Filter for "eltako_esr62pf"
3. Look for error messages with timestamps

**Common Log Messages:**

| Log Message | Meaning | Action |
|-------------|---------|--------|
| `Token expired, refreshing` | Normal token refresh | No action needed |
| `Failed to connect to device` | Network issue | Check network connectivity |
| `Invalid API response` | Device returned unexpected data | Check device firmware |
| `Authentication failed` | Invalid PoP credential | Verify PoP credential |

### Reporting Issues

If you encounter problems not covered here:

1. Enable debug logging (see above)
2. Reproduce the issue
3. Collect relevant log entries
4. Visit [GitHub Issues](https://github.com/tine2k/eltako62pf-hass/issues)
5. Provide:
   - Home Assistant version
   - Integration version
   - Device firmware version (if known)
   - Relevant log entries
   - Steps to reproduce

## Support

- **Issues**: [GitHub Issues](https://github.com/tine2k/eltako62pf-hass/issues)
- **Documentation**: [GitHub Repository](https://github.com/tine2k/eltako62pf-hass)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This is a custom integration and is not officially supported by Eltako or Home Assistant. Use at your own risk.

## Credits

Developed by [@tine2k](https://github.com/tine2k)

## References

- [Product Requirements Document (PRD)](PRD.md) - Detailed technical requirements and specifications
- [Home Assistant Developer Documentation](https://developers.home-assistant.io/)
- [Eltako ESR62PF-IP Documentation](https://www.eltako.com/)
- [Eltako API Specification](https://www.eltako.com/fileadmin/downloads/de/_bedienung/flowbr62ip.json)
- [HACS Documentation](https://hacs.xyz/)
