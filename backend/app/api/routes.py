"""
API routes for Ground Control Hub
"""
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from ..core.config import settings
from ..models.device import (
    DeviceConfig, TelemetryData, ConnectionInfo, TestResult,
    SensorReading
)
from ..services.serial_service import serial_service
from ..websockets.websocket_manager import lora_websocket_manager, websocket_lora_terminal_enhanced

logger = logging.getLogger(__name__)
router = APIRouter()

# WebSocket connections for real-time updates (telemetry)
active_connections: List[WebSocket] = []


# Routes for device management
@router.get("/devices/scan", response_model=Dict[str, List[str]])
async def scan_devices():
    """Scan for available devices"""
    try:
        devices = serial_service.find_devices()
        return devices
    except Exception as e:
        logger.error(f"Error scanning devices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/write")
async def write_device_config(config: DeviceConfig):
    """Write configuration to device"""
    try:
        success = serial_service.write_device_config(config)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to write configuration")
        return {"status": "success", "message": "Configuration written successfully"}
    except Exception as e:
        logger.error(f"Error writing device config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/load/{filename}")
async def load_config_file(filename: str):
    """Load configuration from file"""
    try:
        config_path = settings.gch_directory / "configs" / f"{filename}{settings.config_extension}"
        if not config_path.exists():
            raise HTTPException(status_code=404, detail="Configuration file not found")

        with open(config_path, 'r') as f:
            config_data = json.load(f)

        config = DeviceConfig(**config_data)
        return config
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/save/{filename}")
async def save_config_file(filename: str, config: DeviceConfig):
    """Save configuration to file"""
    try:
        config_path = settings.gch_directory / "configs" / f"{filename}{settings.config_extension}"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(config.model_dump(), f, indent=2, default=str)

        return {"status": "success", "path": str(config_path)}
    except Exception as e:
        logger.error(f"Error saving config file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/list")
async def list_config_files():
    """List available configuration files"""
    try:
        config_dir = settings.gch_directory / "configs"
        config_dir.mkdir(parents=True, exist_ok=True)

        files = []
        for file_path in config_dir.glob(f"*{settings.config_extension}"):
            files.append({
                "name": file_path.stem,
                "path": str(file_path),
                "modified": file_path.stat().st_mtime,
                "size": file_path.stat().st_size
            })

        return files
    except Exception as e:
        logger.error(f"Error listing config files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Testing routes
@router.post("/tests/takeoff", response_model=TestResult)
async def test_takeoff():
    """Execute takeoff test by simulating pressure sensor"""
    try:
        response = serial_service.send_command("TEST_TAKEOFF")

        if not response:
            return TestResult(
                test_name="takeoff",
                status="FAIL",
                message="No response from device"
            )

        status = "OK" if "SUCCESS" in response.upper() else "FAIL"

        return TestResult(
            test_name="takeoff",
            status=status,
            message=response,
            details={"response": response}
        )
    except Exception as e:
        logger.error(f"Error in takeoff test: {e}")
        return TestResult(
            test_name="takeoff",
            status="ERROR",
            message=str(e)
        )


@router.post("/tests/preflight", response_model=List[SensorReading])
async def test_preflight():
    """Execute pre-flight sensor test"""
    try:
        response = serial_service.send_command("TEST_SENSORS")

        if not response:
            raise HTTPException(status_code=500, detail="No response from device")

        try:
            sensor_data = json.loads(response)
            readings = [
                SensorReading(
                    sensor_name=sensor_name,
                    status=data.get("status", "NO_DATA"),
                    value=data.get("value"),
                    unit=data.get("unit")
                )
                for sensor_name, data in sensor_data.items()
            ]
            return readings
        except json.JSONDecodeError:
            readings = []
            for line in response.split('\n'):
                if ':' in line:
                    parts = line.split(':')
                    sensor_name = parts[0].strip()
                    status_value = parts[1].strip()

                    readings.append(SensorReading(
                        sensor_name=sensor_name,
                        status="OK" if "OK" in status_value else "FAIL",
                        value=None,
                        unit=None
                    ))
            return readings

    except Exception as e:
        logger.error(f"Error in pre-flight test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/commands/send")
async def send_command(command: str, use_lora: bool = False):
    """Send raw command to device"""
    try:
        # Send command via WebSocket manager if LoRa and connections exist
        if use_lora and lora_websocket_manager.is_active():
            await lora_websocket_manager.send_command_notification(command)

        response = serial_service.send_command(command, use_lora)

        # Send response via WebSocket if LoRa
        if use_lora and lora_websocket_manager.is_active():
            if response:
                await lora_websocket_manager.broadcast({
                    "type": "command_response",
                    "command": command,
                    "response": response,
                    "timestamp": datetime.now().isoformat()
                })

        return {
            "command": command,
            "response": response,
            "timestamp": datetime.now(),
            "via_lora": use_lora
        }
    except Exception as e:
        logger.error(f"Error sending command: {e}")

        # Send error via WebSocket if LoRa
        if use_lora and lora_websocket_manager.is_active():
            await lora_websocket_manager.send_error(f"Command error: {str(e)}")

        raise HTTPException(status_code=500, detail=str(e))


# Enhanced LoRa bind command with WebSocket updates
@router.post("/lora/bind")
async def bind_lora_satellite():
    """Bind LoRa satellite with real-time updates"""
    try:
        # Notify clients that binding started
        if lora_websocket_manager.is_active():
            await lora_websocket_manager.send_status_update("Starting satellite binding...")

        response = serial_service.send_command("BIND_SATELLITE", use_lora=True)
        success = response and "OK" in response.upper()

        # Notify clients of binding result
        if lora_websocket_manager.is_active():
            message = f"Satellite binding {'successful' if success else 'failed'}"
            await lora_websocket_manager.send_status_update(message)

        return {
            "success": success,
            "response": response,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error binding LoRa satellite: {e}")

        # Notify clients of error
        if lora_websocket_manager.is_active():
            await lora_websocket_manager.send_error(f"Binding error: {str(e)}")

        raise HTTPException(status_code=500, detail=str(e))


# Enhanced blackbox reading with WebSocket updates
@router.post("/lora/blackbox")
async def read_blackbox_via_lora():
    """Read blackbox data via LoRa Link with real-time updates"""
    try:
        # Notify clients that blackbox reading started
        if lora_websocket_manager.is_active():
            await lora_websocket_manager.send_status_update("Starting blackbox data download...")

        response = serial_service.send_command("READ_BLACKBOX", use_lora=True)

        if not response:
            error_msg = "Failed to read blackbox - no response"
            if lora_websocket_manager.is_active():
                await lora_websocket_manager.send_error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

        # Save blackbox data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        blackbox_path = settings.gch_directory / "logs" / f"blackbox_{timestamp}.log"
        blackbox_path.parent.mkdir(parents=True, exist_ok=True)

        with open(blackbox_path, 'w') as f:
            f.write(response)

        # Notify clients of successful download
        success_msg = f"Blackbox downloaded: {len(response)} bytes saved to {blackbox_path.name}"
        if lora_websocket_manager.is_active():
            await lora_websocket_manager.send_status_update(success_msg)

        return {
            "success": True,
            "data_size": len(response),
            "file_path": str(blackbox_path),
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"Error reading blackbox: {e}")

        # Notify clients of error
        if lora_websocket_manager.is_active():
            await lora_websocket_manager.send_error(f"Blackbox read error: {str(e)}")

        raise HTTPException(status_code=500, detail=str(e))


# Enhanced WebSocket endpoint using the manager
@router.websocket("/ws/lora-terminal")
async def websocket_lora_terminal(websocket: WebSocket):
    """WebSocket endpoint for real-time LoRa terminal updates"""
    logger.debug("New connection to LoRa WS")
    await websocket_lora_terminal_enhanced(websocket)


# WebSocket for real-time telemetry
@router.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """WebSocket endpoint for real-time telemetry data"""
    await websocket.accept()
    active_connections.append(websocket)

    if not serial_service.is_monitoring:
        serial_service.start_telemetry_monitoring(broadcast_telemetry)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        if not active_connections:
            serial_service.stop_telemetry_monitoring()


async def broadcast_telemetry(telemetry_data: TelemetryData):
    """Broadcast telemetry data to all connected WebSocket clients"""
    if not active_connections:
        return

    message = telemetry_data.model_dump_json()
    disconnected = []

    for connection in active_connections:
        try:
            await connection.send_text(message)
        except:
            disconnected.append(connection)

    for connection in disconnected:
        active_connections.remove(connection)


# File management routes
@router.get("/files/logs")
async def list_log_files():
    """List available log files"""
    try:
        logs_dir = settings.gch_directory / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        files = []
        for ext in settings.supported_log_formats:
            for file_path in logs_dir.glob(f"*{ext}"):
                files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "modified": file_path.stat().st_mtime,
                    "size": file_path.stat().st_size,
                    "type": ext[1:]
                })

        return sorted(files, key=lambda x: x["modified"], reverse=True)
    except Exception as e:
        logger.error(f"Error listing log files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": settings.version
    }


@router.post("/devices/connect")
async def connect_device(device_type: str, port: Optional[str] = None):
    """Connect to device or LoRa Link"""
    try:
        if device_type == "device":
            success = serial_service.connect_device(port)
        elif device_type == "lora_link":
            success = serial_service.connect_lora_link(port)
        else:
            raise HTTPException(status_code=400, detail="Invalid device type")

        if not success:
            raise HTTPException(status_code=500, detail="Failed to connect")

        # Notify WebSocket clients of connection
        if device_type == "lora_link" and lora_websocket_manager.is_active():
            await lora_websocket_manager.send_status_update(
                f"Connected to LoRa Link on {port or 'auto-detected port'}"
            )

        return {"status": "connected", "device_type": device_type, "port": port}
    except Exception as e:
        logger.error(f"Error connecting to {device_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/devices/disconnect")
async def disconnect_device(device_type: str):
    """Disconnect from device or LoRa Link"""
    try:
        if device_type == "device":
            serial_service.disconnect_device()
        elif device_type == "lora_link":
            serial_service.disconnect_lora_link()
        else:
            raise HTTPException(status_code=400, detail="Invalid device type")

        # Notify WebSocket clients of disconnection
        if device_type == "lora_link" and lora_websocket_manager.is_active():
            await lora_websocket_manager.send_status_update("Disconnected from LoRa Link")

        return {"status": "disconnected", "device_type": device_type}
    except Exception as e:
        logger.error(f"Error disconnecting from {device_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/devices/status", response_model=ConnectionInfo)
async def get_device_status():
    """Get current device connection status"""
    return serial_service.get_connection_status()


@router.post("/devices/ping")
async def ping_device(use_lora: bool = False):
    """Ping device to test connectivity"""
    try:
        success = serial_service.ping_device(use_lora)
        return {"success": success, "timestamp": datetime.now()}
    except Exception as e:
        logger.error(f"Error pinging device: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Configuration management routes
@router.get("/config/read", response_model=DeviceConfig)
async def read_device_config():
    """Read current device configuration"""
    try:
        config = serial_service.read_device_config()
        if not config:
            raise HTTPException(status_code=500, detail="Failed to read configuration")
        return config
    except Exception as e:
        logger.error(f"Error reading device config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
