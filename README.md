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

## Known Limitations

- API tokens are valid for 15 minutes and are automatically refreshed
- The device uses self-signed SSL certificates (expected and supported)
- Polling is disabled by default to reduce API calls
- Maximum response time: ~500ms for relay operations

## Troubleshooting

### Connection Issues

If you experience connection issues:

1. Verify the IP address and port are correct
2. Ensure the PoP credential is correct
3. Check that the device is reachable on your network
4. Review Home Assistant logs for detailed error messages

### Authentication Errors

If you see authentication errors:

1. Verify your PoP credential is correct
2. The integration will automatically refresh tokens
3. Check the logs for specific error messages

### Enable Debug Logging

Add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.eltako_esr62pf: debug
```

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

- [Home Assistant Developer Documentation](https://developers.home-assistant.io/)
- [Eltako ESR62PF-IP Documentation](https://www.eltako.com/)
- [HACS Documentation](https://hacs.xyz/)
