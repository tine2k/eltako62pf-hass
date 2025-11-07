# Eltako ESR62PF-IP Integration

Control your Eltako ESR62PF-IP relay devices directly from Home Assistant.

## About

This integration enables seamless control of Eltako ESR62PF-IP network-connected relay devices through Home Assistant. The Eltako ESR62PF-IP provides remote switching capabilities for building automation and smart home applications.

## Features

- **Simple Setup**: Easy UI-based configuration flow
- **Automatic Discovery**: Finds all relays connected to your device
- **Switch Control**: Control relays as standard Home Assistant switches
- **Flexible Polling**: Optional state synchronization (disabled by default)
- **Secure**: Support for self-signed SSL certificates
- **Reliable**: Automatic token refresh and error recovery

## Installation

### Via HACS (Recommended)

1. Add this repository as a custom repository in HACS
2. Search for "Eltako ESR62PF-IP"
3. Click "Download"
4. Restart Home Assistant
5. Add the integration via Settings → Devices & Services

### Manual Installation

1. Copy `custom_components/eltako_esr62pf` to your Home Assistant config directory
2. Restart Home Assistant
3. Add the integration via Settings → Devices & Services

## Configuration

When adding the integration, you'll need:

- **IP Address**: Your Eltako device's IP address
- **Port**: Usually 443 (default)
- **PoP**: Your device's Proof of Possession credential

The integration will automatically discover all relays and create switch entities.

## Optional Configuration

After setup, you can configure:

- **Polling Interval**: How often to check device state (disabled by default)
  - Recommended: Keep disabled for best performance
  - If enabled: 30-60 seconds recommended

## Usage

Control your relays using standard Home Assistant switch services:

- `switch.turn_on`
- `switch.turn_off`
- `switch.toggle`

Perfect for automations, scenes, and dashboards!

## Support

For issues, questions, or feature requests, please visit the [GitHub repository](https://github.com/tine2k/eltako62pf-hass).
