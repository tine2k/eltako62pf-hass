"""Constants for Eltako ESR62PF-IP integration."""

# Domain
DOMAIN = "eltako_esr62pf"

# Config Flow
CONF_IP_ADDRESS = "ip_address"
CONF_PORT = "port"
CONF_POP_CREDENTIAL = "pop_credential"

# API Configuration
API_TOKEN_TTL = 900  # 15 minutes in seconds
DEVICE_CACHE_TTL = 60  # Device list cache TTL in seconds
DEFAULT_PORT = 443
DEFAULT_TIMEOUT = 10  # seconds
DEFAULT_USERNAME = "admin"  # Fixed username for Eltako devices

# Retry Configuration
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # Exponential backoff multiplier

# API Endpoints
ENDPOINT_LOGIN = "/api/v0/login"
ENDPOINT_DEVICES = "/api/v0/devices"
ENDPOINT_RELAY = "/api/v0/devices/{device_guid}/functions/relay"

# Relay States
RELAY_STATE_ON = "on"
RELAY_STATE_OFF = "off"
