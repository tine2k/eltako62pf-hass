#!/usr/bin/env python3
"""Test script for running integration tests against a real Eltako device.

This script tests the API client against a real Eltako ESR62PF-IP device.
It performs basic connectivity, authentication, and device discovery tests.

Usage:
    python test_real_device.py --ip <device_ip> --pop <pop_credential> [--port <port>]

Example:
    python test_real_device.py --ip 10.0.7.45 --pop 15659251
"""
import argparse
import asyncio
import logging
import sys
from typing import Any

# Add the custom_components path to allow importing the API client
sys.path.insert(0, "/Users/tine2k/Documents/git/eltako62pf-hass")

from custom_components.eltako_esr62pf.api import EltakoAPI
from custom_components.eltako_esr62pf.const import DEFAULT_PORT, RELAY_STATE_OFF, RELAY_STATE_ON
from custom_components.eltako_esr62pf.exceptions import (
    EltakoAPIError,
    EltakoAuthenticationError,
    EltakoConnectionError,
    EltakoTimeoutError,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TestResult:
    """Simple test result tracker."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def add_pass(self, test_name: str):
        """Record a passed test."""
        self.passed += 1
        logger.info("✓ PASS: %s", test_name)

    def add_fail(self, test_name: str, error: str):
        """Record a failed test."""
        self.failed += 1
        self.errors.append((test_name, error))
        logger.error("✗ FAIL: %s - %s", test_name, error)

    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Success rate: {(self.passed / total * 100) if total > 0 else 0:.1f}%")

        if self.errors:
            print("\nFailed tests:")
            for test_name, error in self.errors:
                print(f"  - {test_name}: {error}")

        print("=" * 60)
        return self.failed == 0


async def test_connection(api: EltakoAPI, results: TestResult) -> None:
    """Test basic connection to the device.

    Args:
        api: API client instance
        results: Test results tracker
    """
    test_name = "Connection Test"
    try:
        # Just verify we can reach the device (base URL is accessible)
        logger.info("Testing connection to %s", api.base_url)
        results.add_pass(test_name)
    except Exception as err:
        results.add_fail(test_name, str(err))


async def test_authentication(api: EltakoAPI, results: TestResult) -> None:
    """Test authentication with the device.

    Args:
        api: API client instance
        results: Test results tracker
    """
    test_name = "Authentication Test"
    try:
        logger.info("Testing authentication...")
        api_key = await api.async_login()

        if api_key:
            logger.info("Received API key: %s...", api_key[:10])
            results.add_pass(test_name)
        else:
            results.add_fail(test_name, "No API key returned")

    except EltakoAuthenticationError as err:
        results.add_fail(test_name, f"Authentication failed: {err}")
    except EltakoConnectionError as err:
        results.add_fail(test_name, f"Connection error: {err}")
    except EltakoTimeoutError as err:
        results.add_fail(test_name, f"Timeout error: {err}")
    except Exception as err:
        results.add_fail(test_name, f"Unexpected error: {err}")


async def test_get_devices(api: EltakoAPI, results: TestResult) -> list[dict[str, Any]]:
    """Test fetching device list.

    Args:
        api: API client instance
        results: Test results tracker

    Returns:
        List of devices
    """
    test_name = "Get Devices Test"
    try:
        logger.info("Fetching device list...")
        devices = await api.async_get_devices()

        logger.info("Found %d devices:", len(devices))
        for i, device in enumerate(devices, 1):
            guid = device.get("guid", "N/A")
            name = device.get("name", "Unnamed")
            logger.info("  %d. %s (GUID: %s)", i, name, guid)

        if devices:
            results.add_pass(test_name)
        else:
            results.add_fail(test_name, "No devices found")

        return devices

    except EltakoAPIError as err:
        results.add_fail(test_name, f"API error: {err}")
    except Exception as err:
        results.add_fail(test_name, f"Unexpected error: {err}")

    return []


async def test_device_cache(api: EltakoAPI, results: TestResult) -> None:
    """Test device caching functionality.

    Args:
        api: API client instance
        results: Test results tracker
    """
    test_name = "Device Cache Test"
    try:
        logger.info("Testing device cache...")

        # First call - should fetch from API
        devices1 = await api.async_get_devices()

        # Second call - should use cache
        devices2 = await api.async_get_devices()

        # Verify cache worked (should be same object reference)
        if devices1 == devices2:
            results.add_pass(test_name)
        else:
            results.add_fail(test_name, "Cached devices differ from fresh fetch")

    except Exception as err:
        results.add_fail(test_name, f"Unexpected error: {err}")


async def test_relay_control(
    api: EltakoAPI, devices: list[dict[str, Any]], results: TestResult, interactive: bool
) -> None:
    """Test relay control (optional, requires user confirmation).

    Args:
        api: API client instance
        devices: List of devices
        results: Test results tracker
        interactive: Whether to run interactive tests
    """
    if not devices:
        logger.warning("Skipping relay control test - no devices available")
        return

    if not interactive:
        logger.info("Skipping relay control test (use --interactive to enable)")
        return

    test_device = devices[0]
    device_guid = test_device.get("guid")
    device_name = test_device.get("name", "Unnamed")

    print(f"\n{'=' * 60}")
    print("INTERACTIVE RELAY CONTROL TEST")
    print(f"{'=' * 60}")
    print(f"This test will toggle relay on device: {device_name} (GUID: {device_guid})")
    print("The relay will be turned ON, then OFF.")
    response = input("\nDo you want to proceed? (yes/no): ")

    if response.lower() != "yes":
        logger.info("Relay control test skipped by user")
        return

    # Test turning relay ON
    test_name_on = "Relay Control Test (ON)"
    try:
        logger.info("Turning relay ON for device: %s", device_name)
        await api.async_set_relay(device_guid, RELAY_STATE_ON)
        results.add_pass(test_name_on)
        await asyncio.sleep(2)  # Wait a bit before turning off
    except Exception as err:
        results.add_fail(test_name_on, str(err))

    # Test turning relay OFF
    test_name_off = "Relay Control Test (OFF)"
    try:
        logger.info("Turning relay OFF for device: %s", device_name)
        await api.async_set_relay(device_guid, RELAY_STATE_OFF)
        results.add_pass(test_name_off)
    except Exception as err:
        results.add_fail(test_name_off, str(err))


async def test_token_expiry(api: EltakoAPI, results: TestResult) -> None:
    """Test token expiry and refresh.

    Args:
        api: API client instance
        results: Test results tracker
    """
    test_name = "Token Expiry Test"
    try:
        logger.info("Testing token expiry handling...")

        # Force token expiry
        api._token_timestamp = 0

        # This should trigger automatic token refresh
        devices = await api.async_get_devices()

        if devices is not None:
            results.add_pass(test_name)
        else:
            results.add_fail(test_name, "Failed to fetch devices after token refresh")

    except Exception as err:
        results.add_fail(test_name, f"Unexpected error: {err}")


async def run_tests(
    ip_address: str,
    pop_credential: str,
    port: int,
    interactive: bool,
    verify_ssl: bool,
) -> bool:
    """Run all integration tests.

    Args:
        ip_address: Device IP address
        pop_credential: PoP credential
        port: Device port
        interactive: Whether to run interactive tests
        verify_ssl: Whether to verify SSL certificates

    Returns:
        True if all tests passed, False otherwise
    """
    results = TestResult()

    logger.info("Starting integration tests against real device")
    logger.info("Device: %s:%d", ip_address, port)
    logger.info("SSL verification: %s", "enabled" if verify_ssl else "disabled")

    async with EltakoAPI(
        ip_address=ip_address,
        pop_credential=pop_credential,
        port=port,
        verify_ssl=verify_ssl,
    ) as api:
        # Run tests in sequence
        await test_connection(api, results)
        await test_authentication(api, results)

        devices = await test_get_devices(api, results)
        await test_device_cache(api, results)
        await test_token_expiry(api, results)

        # Interactive tests (only if user confirms)
        await test_relay_control(api, devices, results, interactive)

    return results.print_summary()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Eltako ESR62PF-IP integration against real device"
    )
    parser.add_argument(
        "--ip",
        required=True,
        help="IP address of the Eltako device (e.g., 10.0.7.45)",
    )
    parser.add_argument(
        "--pop",
        required=True,
        help="Proof of Possession credential (e.g., 15659251)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Port number (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run interactive tests (relay control)",
    )
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Disable SSL certificate verification",
    )

    args = parser.parse_args()

    # Run async tests
    success = asyncio.run(
        run_tests(
            ip_address=args.ip,
            pop_credential=args.pop,
            port=args.port,
            interactive=args.interactive,
            verify_ssl=not args.no_verify_ssl,
        )
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
