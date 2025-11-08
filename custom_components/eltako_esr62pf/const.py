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

# Coordinator Configuration
CONF_POLL_INTERVAL = "poll_interval"
MIN_POLL_INTERVAL = 10  # Minimum polling interval in seconds
DEFAULT_POLL_INTERVAL = 30  # Default polling interval in seconds (recommended 30-60)

# Error Handling Configuration
MAX_CONSECUTIVE_FAILURES = 3  # Number of failures before showing persistent notification
NOTIFICATION_ID_PREFIX = "eltako_esr62pf_error"  # Prefix for persistent notification IDs

# Error Messages
ERROR_MSG_CONNECTION = "Cannot reach Eltako device at {ip}:{port}. Check network and device power."
ERROR_MSG_AUTHENTICATION = "Authentication failed. Verify the PoP credential in integration settings."
ERROR_MSG_TIMEOUT = "Device not responding. Check network connection and device status."
ERROR_MSG_API_ERROR = "API error occurred: {error}. Please check device logs."
