"""
Enhanced Serial communication service for device and LoRa Link communication
with real-time data streaming capabilities
"""

import json
import logging
import queue
import time
from datetime import datetime
from threading import Thread, Event, Lock
from typing import Optional, List, Dict, Callable, Any

import serial
import serial.tools.list_ports

from ..core.config import settings
from ..models.device import DeviceConfig, TelemetryData, ConnectionInfo, DeviceStatus

logger = logging.getLogger(__name__)


class EnhancedSerialService:
    """Enhanced serial communication service with real-time streaming"""

    def __init__(self):
        self.device_port: Optional[serial.Serial] = None
        self.lora_port: Optional[serial.Serial] = None
        self.telemetry_callback: Optional[Callable] = None
        self.lora_data_callback: Optional[Callable] = None

        # Monitoring threads and events
        self.is_monitoring = False
        self.is_lora_monitoring = False
        self.monitor_thread: Optional[Thread] = None
        self.lora_monitor_thread: Optional[Thread] = None
        self.stop_event = Event()
        self.lora_stop_event = Event()

        # Thread-safe data queues for real-time streaming
        self.lora_data_queue = queue.Queue(maxsize=100)  # Limit queue size
        self.telemetry_queue = queue.Queue(maxsize=100)

        # Locks for thread safety
        self.device_lock = Lock()
        self.lora_lock = Lock()

        # Buffer for incomplete messages
        self.lora_buffer = ""
        self.device_buffer = ""

    def find_devices(self) -> Dict[str, List[str]]:
        """Find available serial devices by VID:PID"""
        devices = {"device": [], "lora_link": []}

        try:
            ports = serial.tools.list_ports.comports()
            for port in ports:
                if port.vid and port.pid:
                    vid_pid = f"{port.vid:04X}:{port.pid:04X}"
                    logger.debug(f"Found device: {port.device} ({vid_pid}) - {port.description}")

                    # Check for stratospheric device (STM32F401)
                    if (f"{port.vid:04X}" == settings.device_vid and
                            f"{port.pid:04X}" == settings.device_pid):
                        devices["device"].append(port.device)
                        logger.info(f"Found stratospheric device: {port.device}")

                    # Check for LoRa Link (STM32F103)
                    if (f"{port.vid:04X}" == settings.lora_vid and
                            f"{port.pid:04X}" == settings.lora_pid):
                        devices["lora_link"].append(port.device)
                        logger.info(f"Found LoRa Link: {port.device}")

        except Exception as e:
            logger.error(f"Error scanning for devices: {e}")

        return devices

    def connect_device(self, port: Optional[str] = None) -> bool:
        """Connect to stratospheric device"""
        with self.device_lock:
            try:
                if not port:
                    devices = self.find_devices()
                    if not devices["device"]:
                        logger.warning("No stratospheric device found")
                        return False
                    port = devices["device"][0]

                # Close existing connection
                if self.device_port and self.device_port.is_open:
                    self.device_port.close()

                self.device_port = serial.Serial(
                    port=port,
                    baudrate=settings.serial_baudrate,
                    timeout=settings.serial_timeout,
                    write_timeout=settings.serial_timeout
                )

                # Clear any existing data in buffers
                self.device_port.reset_input_buffer()
                self.device_port.reset_output_buffer()
                self.device_buffer = ""

                logger.info(f"Connected to device on {port}")
                return True

            except Exception as e:
                logger.error(f"Failed to connect to device: {e}")
                return False

    def connect_lora_link(self, port: Optional[str] = None) -> bool:
        """Connect to LoRa Link module"""
        with self.lora_lock:
            try:
                if not port:
                    devices = self.find_devices()
                    if not devices["lora_link"]:
                        logger.warning("No LoRa Link found")
                        return False
                    port = devices["lora_link"][0]

                # Close existing connection
                if self.lora_port and self.lora_port.is_open:
                    self.lora_port.close()

                self.lora_port = serial.Serial(
                    port=port,
                    baudrate=settings.serial_baudrate,
                    timeout=0.1,  # Reduced timeout for more responsive reading
                    write_timeout=settings.serial_timeout
                )

                # Clear any existing data in buffers
                self.lora_port.reset_input_buffer()
                self.lora_port.reset_output_buffer()
                self.lora_buffer = ""

                # Clear the queue
                while not self.lora_data_queue.empty():
                    try:
                        self.lora_data_queue.get_nowait()
                    except queue.Empty:
                        break

                logger.info(f"Connected to LoRa Link on {port}")

                # Start LoRa monitoring thread for real-time data
                self.start_lora_monitoring()

                return True

            except Exception as e:
                logger.error(f"Failed to connect to LoRa Link: {e}")
                return False

    def disconnect_device(self):
        """Disconnect from stratospheric device"""
        with self.device_lock:
            if self.device_port and self.device_port.is_open:
                self.device_port.close()
                self.device_buffer = ""
                logger.info("Disconnected from device")

    def disconnect_lora_link(self):
        """Disconnect from LoRa Link"""
        # Stop monitoring first
        self.stop_lora_monitoring()

        with self.lora_lock:
            if self.lora_port and self.lora_port.is_open:
                self.lora_port.close()
                self.lora_buffer = ""
                logger.info("Disconnected from LoRa Link")

    def send_command(self, command: str, use_lora: bool = False) -> Optional[str]:
        """Send command to device or LoRa Link with enhanced response handling"""
        try:
            port = self.lora_port if use_lora else self.device_port
            lock = self.lora_lock if use_lora else self.device_lock

            with lock:
                if not port or not port.is_open:
                    logger.error(f"{'LoRa Link' if use_lora else 'Device'} not connected")
                    return None

                # Clear input buffer before sending command
                port.reset_input_buffer()

                # Send command with proper line ending
                command_bytes = (command + "\n").encode('utf-8')
                port.write(command_bytes)
                port.flush()

                logger.info(f"Sent command: {command} (via {'LoRa' if use_lora else 'USB'})")

                # For LoRa commands, return immediately as response will come via monitoring
                if use_lora:
                    return None

                # Wait for response with timeout for direct USB commands
                response_lines = []
                start_time = time.time()
                timeout = 5.0  # 5 second timeout for command responses
                partial_line = ""

                while time.time() - start_time < timeout:
                    if port.in_waiting > 0:
                        chunk = port.read(port.in_waiting).decode('utf-8', errors='ignore')
                        partial_line += chunk

                        # Process complete lines
                        while '\n' in partial_line:
                            line, partial_line = partial_line.split('\n', 1)
                            line = line.strip()
                            if line:
                                response_lines.append(line)

                                # Check for common command completion indicators
                                if any(indicator in line.upper() for indicator in
                                       ['OK', 'ERROR', 'DONE', 'FAIL', 'SUCCESS']):
                                    response = '\n'.join(response_lines)
                                    logger.debug(f"Command response: {response}")
                                    return response

                    time.sleep(0.05)  # Small delay to prevent excessive CPU usage

                # Add any remaining partial line
                if partial_line.strip():
                    response_lines.append(partial_line.strip())

                # Return whatever we got if timeout reached
                response = '\n'.join(response_lines) if response_lines else None
                logger.debug(f"Command timeout, partial response: {response}")
                return response

        except Exception as e:
            logger.error(f"Error sending command '{command}': {e}")
            return None

    def start_lora_monitoring(self):
        """Start monitoring LoRa Link for incoming data"""
        if self.is_lora_monitoring:
            return

        self.is_lora_monitoring = True
        self.lora_stop_event.clear()

        self.lora_monitor_thread = Thread(
            target=self._lora_monitor_loop,
            daemon=True,
            name="LoRaMonitor"
        )
        self.lora_monitor_thread.start()

        logger.info("Started LoRa Link monitoring")

    def stop_lora_monitoring(self):
        """Stop monitoring LoRa Link"""
        if not self.is_lora_monitoring:
            return

        self.is_lora_monitoring = False
        self.lora_stop_event.set()

        if self.lora_monitor_thread and self.lora_monitor_thread.is_alive():
            self.lora_monitor_thread.join(timeout=2.0)

        logger.info("Stopped LoRa Link monitoring")

    def _lora_monitor_loop(self):
        """Background loop for LoRa Link monitoring"""
        logger.info("LoRa monitoring loop started")

        while self.is_lora_monitoring and not self.lora_stop_event.is_set():
            try:
                if not self.lora_port or not self.lora_port.is_open:
                    time.sleep(0.5)
                    continue

                # Check for incoming data
                try:
                    if self.lora_port.in_waiting > 0:
                        with self.lora_lock:
                            # Read available data with timeout
                            raw_data = self.lora_port.read(
                                min(self.lora_port.in_waiting, 1024)  # Limit read size
                            ).decode('utf-8', errors='ignore')

                            if raw_data:
                                logger.debug(f"Received raw LoRa data: {repr(raw_data)}")
                                # Add to buffer and process complete lines
                                self.lora_buffer += raw_data
                                self._process_lora_buffer()

                except serial.SerialException as e:
                    logger.error(f"Serial error in LoRa monitoring: {e}")
                    time.sleep(1.0)
                    continue
                except Exception as e:
                    logger.error(f"Error reading LoRa data: {e}")

                # Small delay to prevent excessive CPU usage
                time.sleep(0.01)

            except Exception as e:
                logger.error(f"Error in LoRa monitoring loop: {e}")
                time.sleep(1.0)

        logger.info("LoRa monitoring loop ended")

    def _process_lora_buffer(self):
        """Process buffered LoRa data and extract complete messages"""
        processed_lines = 0
        max_lines_per_process = 10  # Prevent processing too many lines at once

        while '\n' in self.lora_buffer and processed_lines < max_lines_per_process:
            line, self.lora_buffer = self.lora_buffer.split('\n', 1)
            line = line.strip()
            processed_lines += 1

            if line:  # Only process non-empty lines
                data_item = {
                    'type': 'terminal_output',
                    'content': line,
                    'timestamp': datetime.now().isoformat()
                }
                logger.debug(f"Processing LoRa line: '{line}'")

                # Add to queue for processing
                try:
                    self.lora_data_queue.put(data_item, block=False)
                    logger.debug(f"Successfully added to LoRa queue: {data_item}")
                except queue.Full:
                    # Queue is full, remove oldest items to make space
                    try:
                        # Remove up to 5 old items to make space
                        for _ in range(5):
                            removed_item = self.lora_data_queue.get_nowait()
                            logger.debug(f"Removed old item from full queue: {removed_item}")

                        # Try to add the new item again
                        self.lora_data_queue.put(data_item, block=False)
                        logger.debug(f"Added to LoRa queue after cleanup: {data_item}")
                    except queue.Empty:
                        # Queue became empty, try to add directly
                        try:
                            self.lora_data_queue.put(data_item, block=False)
                        except queue.Full:
                            logger.warning("LoRa queue is still full after cleanup, dropping message")
                    except Exception as e:
                        logger.error(f"Error managing LoRa queue: {e}")

    def get_lora_data(self) -> Optional[Dict[str, Any]]:
        """Get next available LoRa data from queue (non-blocking)"""
        try:
            data = self.lora_data_queue.get_nowait()
            logger.debug(f"Retrieved LoRa data from queue: {data}")
            return data
        except queue.Empty:
            return None

    def has_lora_data(self) -> bool:
        """Check if LoRa data is available"""
        result = not self.lora_data_queue.empty()
        if result:
            logger.debug(f"LoRa data available, queue size: {self.lora_data_queue.qsize()}")
        return result

    def get_queue_size(self) -> int:
        """Get current queue size for debugging"""
        return self.lora_data_queue.qsize()

    def set_lora_data_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Set callback for LoRa data updates"""
        self.lora_data_callback = callback

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

            # Parse JSON response
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
            return response and "OK" in response.upper()

        except Exception as e:
            logger.error(f"Error writing device config: {e}")
            return False

    def start_telemetry_monitoring(self, callback: Callable[[TelemetryData], None]):
        """Start monitoring telemetry data"""
        self.telemetry_callback = callback
        self.is_monitoring = True
        self.stop_event.clear()

        self.monitor_thread = Thread(
            target=self._telemetry_monitor_loop,
            daemon=True,
            name="TelemetryMonitor"
        )
        self.monitor_thread.start()

        logger.info("Started telemetry monitoring")

    def stop_telemetry_monitoring(self):
        """Stop monitoring telemetry data"""
        self.is_monitoring = False
        self.stop_event.set()

        if self.monitor_thread and self.monitor_thread.is_alive():
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
                time.sleep(1.0)

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

    def get_port_info(self, use_lora: bool = False) -> Optional[Dict[str, str]]:
        """Get detailed port information"""
        port = self.lora_port if use_lora else self.device_port
        if not port or not port.is_open:
            return None

        return {
            "name": port.name,
            "baudrate": str(port.baudrate),
            "timeout": str(port.timeout),
            "is_open": str(port.is_open),
            "in_waiting": str(port.in_waiting),
            "out_waiting": str(port.out_waiting) if hasattr(port, 'out_waiting') else "N/A"
        }

    def __del__(self):
        """Cleanup on destruction"""
        self.stop_telemetry_monitoring()
        self.stop_lora_monitoring()
        self.disconnect_device()
        self.disconnect_lora_link()


# Global enhanced serial service instance
serial_service = EnhancedSerialService()
