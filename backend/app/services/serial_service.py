"""
Serial communication service for device and LoRa Link communication
"""

import serial
import serial.tools.list_ports
import asyncio
import logging
import json
from typing import Optional, List, Dict, Callable
from datetime import datetime
from threading import Thread, Event
import time

from ..core.config import settings
from ..models.device import DeviceConfig, TelemetryData, ConnectionInfo, DeviceStatus

logger = logging.getLogger(__name__)


class SerialService:
    """Handles serial communication with stratospheric device and LoRa Link"""

    def __init__(self):
        self.device_port: Optional[serial.Serial] = None
        self.lora_port: Optional[serial.Serial] = None
        self.telemetry_callback: Optional[Callable] = None
        self.is_monitoring = False
        self.monitor_thread: Optional[Thread] = None
        self.stop_event = Event()

    def find_devices(self) -> Dict[str, List[str]]:
        """Find available serial devices by VID:PID"""
        devices = {"device": [], "lora_link": []}

        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if port.vid and port.pid:
                    vid_pid = f"{port.vid:04X}:{port.pid:04X}"
                    logger.debug(f"Found device: {port.device} ({vid_pid})")

                    # Check for stratospheric device (STM32F401)
                    if (f"{port.vid:04X}" == settings.device_vid and
                            f"{port.pid:04X}" == settings.device_pid):
                        devices["device"].append(port.device)

                    # Check for LoRa Link (STM32F103)
                    if (f"{port.vid:04X}" == settings.lora_vid and
                            f"{port.pid:04X}" == settings.lora_pid):
                        devices["lora_link"].append(port.device)

        except Exception as e:
            logger.error(f"Error scanning for devices: {e}")

        return devices

    def connect_device(self, port: Optional[str] = None) -> bool:
        """Connect to stratospheric device"""
        try:
            if not port:
                devices = self.find_devices()
                if not devices["device"]:
                    logger.warning("No stratospheric device found")
                    return False
                port = devices["device"][0]

            if self.device_port and self.device_port.is_open:
                self.device_port.close()

            self.device_port = serial.Serial(
                port=port,
                baudrate=settings.serial_baudrate,
                timeout=settings.serial_timeout,
                write_timeout=settings.serial_timeout
            )

            logger.info(f"Connected to device on {port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to device: {e}")
            return False

    def connect_lora_link(self, port: Optional[str] = None) -> bool:
        """Connect to LoRa Link module"""
        try:
            if not port:
                devices = self.find_devices()
                if not devices["lora_link"]:
                    logger.warning("No LoRa Link found")
                    return False
                port = devices["lora_link"][0]

            if self.lora_port and self.lora_port.is_open:
                self.lora_port.close()

            self.lora_port = serial.Serial(
                port=port,
                baudrate=settings.serial_baudrate,
                timeout=settings.serial_timeout,
                write_timeout=settings.serial_timeout
            )

            logger.info(f"Connected to LoRa Link on {port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to LoRa Link: {e}")
            return False

    def disconnect_device(self):
        """Disconnect from stratospheric device"""
        if self.device_port and self.device_port.is_open:
            self.device_port.close()
            logger.info("Disconnected from device")

    def disconnect_lora_link(self):
        """Disconnect from LoRa Link"""
        if self.lora_port and self.lora_port.is_open:
            self.lora_port.close()
            logger.info("Disconnected from LoRa Link")

    def send_command(self, command: str, use_lora: bool = False) -> Optional[str]:
        """Send command to device or LoRa Link"""
        try:
            port = self.lora_port if use_lora else self.device_port
            if not port or not port.is_open:
                logger.error(f"{'LoRa Link' if use_lora else 'Device'} not connected")
                return None

            # Send command
            port.write((command + "\n").encode())
            port.flush()

            # Wait for response
            time.sleep(0.1)
            response = ""
            while port.in_waiting > 0:
                response += port.read(port.in_waiting).decode('utf-8', errors='ignore')
                time.sleep(0.01)

            logger.debug(f"Command: {command}, Response: {response.strip()}")
            return response.strip()

        except Exception as e:
            logger.error(f"Error sending command '{command}': {e}")
            return None

    def read_device_config(self) -> Optional[DeviceConfig]:
        """Read current device configuration via USB"""
        try:
            if not self.device_port or not self.device_port.is_open:
                logger.error("Device not connected")
                return None

            # Send configuration read command
            response = self.send_command("GET_CONFIG")
            if not response:
                return None

            # Parse JSON response (assuming device returns JSON)
            try:
                config_data = json.loads(response)
                return DeviceConfig(**config_data)
            except json.JSONDecodeError:
                logger.error("Failed to parse device configuration")
                return None

        except Exception as e:
            logger.error(f"Error reading device config: {e}")
            return None

    def write_device_config(self, config: DeviceConfig) -> bool:
        """Write configuration to device via USB"""
        try:
            if not self.device_port or not self.device_port.is_open:
                logger.error("Device not connected")
                return False

            # Convert config to JSON
            config_json = config.model_dump_json()

            # Send configuration write command
            command = f"SET_CONFIG {config_json}"
            response = self.send_command(command)

            # Check if write was successful
            return response and "OK" in response

        except Exception as e:
            logger.error(f"Error writing device config: {e}")
            return False

    def start_telemetry_monitoring(self, callback: Callable[[TelemetryData], None]):
        """Start monitoring telemetry data"""
        self.telemetry_callback = callback
        self.is_monitoring = True
        self.stop_event.clear()

        self.monitor_thread = Thread(target=self._telemetry_monitor_loop, daemon=True)
        self.monitor_thread.start()

        logger.info("Started telemetry monitoring")

    def stop_telemetry_monitoring(self):
        """Stop monitoring telemetry data"""
        self.is_monitoring = False
        self.stop_event.set()

        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

        logger.info("Stopped telemetry monitoring")

    def _telemetry_monitor_loop(self):
        """Background loop for telemetry monitoring"""
        while self.is_monitoring and not self.stop_event.is_set():
            try:
                # Try to read from device first, then LoRa Link
                data = None

                if self.device_port and self.device_port.is_open:
                    data = self._read_telemetry_data(self.device_port)
                elif self.lora_port and self.lora_port.is_open:
                    data = self._read_telemetry_data(self.lora_port)

                if data and self.telemetry_callback:
                    self.telemetry_callback(data)

                # Wait for next update cycle
                time.sleep(settings.telemetry_update_interval)

            except Exception as e:
                logger.error(f"Error in telemetry monitoring: {e}")
                time.sleep(1.0)  # Wait before retry

    def _read_telemetry_data(self, port: serial.Serial) -> Optional[TelemetryData]:
        """Read and parse telemetry data from serial port"""
        try:
            if port.in_waiting == 0:
                return None

            # Read available data
            raw_data = port.read(port.in_waiting).decode('utf-8', errors='ignore')

            # Look for complete JSON telemetry packets
            lines = raw_data.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    try:
                        telemetry_dict = json.loads(line)
                        return TelemetryData(**telemetry_dict)
                    except (json.JSONDecodeError, ValueError):
                        continue

            return None

        except Exception as e:
            logger.error(f"Error reading telemetry data: {e}")
            return None

    def get_connection_status(self) -> ConnectionInfo:
        """Get current connection status"""
        if self.device_port and self.device_port.is_open:
            return ConnectionInfo(
                status=DeviceStatus.CONNECTED_USB,
                port=self.device_port.name,
                device_type="device",
                last_seen=datetime.now()
            )
        elif self.lora_port and self.lora_port.is_open:
            return ConnectionInfo(
                status=DeviceStatus.CONNECTED_LORA,
                port=self.lora_port.name,
                device_type="lora_link",
                last_seen=datetime.now()
            )
        else:
            return ConnectionInfo(status=DeviceStatus.DISCONNECTED)

    def ping_device(self, use_lora: bool = False) -> bool:
        """Ping device to check connectivity"""
        response = self.send_command("PING", use_lora)
        return response is not None and "PONG" in response.upper()

    def __del__(self):
        """Cleanup on destruction"""
        self.stop_telemetry_monitoring()
        self.disconnect_device()
        self.disconnect_lora_link()


# Global serial service instance
serial_service = SerialService()