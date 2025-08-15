"""
Data models for stratospheric device configuration and telemetry
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime


class LoRaConfig(BaseModel):
    """LoRa radio configuration parameters"""
    frequency: int = Field(default=433000000, description="Frequency in Hz")
    bandwidth: int = Field(default=7, ge=0, le=9, description="Bandwidth index (0-9)")
    spreading_factor: int = Field(default=7, ge=6, le=12, description="Spreading factor (6-12)")
    coding_rate: int = Field(default=0, ge=0, le=3, description="Coding rate (0=4/5, 1=4/6, 2=4/7, 3=4/8)")
    header_mode: int = Field(default=0, ge=0, le=1, description="Header mode (0=explicit, 1=fixed)")
    crc_enabled: int = Field(default=1, ge=0, le=1, description="CRC enabled (0/1)")
    low_data_rate_optimize: int = Field(default=0, ge=0, le=1, description="Low data rate optimization (0/1)")
    preamble_length: int = Field(default=8, ge=4, description="Preamble length (min 4)")
    payload_length: int = Field(default=255, ge=1, le=255, description="Payload length (max 255)")
    tx_power: int = Field(default=15, ge=0, le=15, description="TX power (0-15)")
    tx_addr: int = Field(default=0, ge=0, le=255, description="TX FIFO base address")
    rx_addr: int = Field(default=0, ge=0, le=255, description="RX FIFO base address")


class SafeSettings(BaseModel):
    """Safe settings from user.h - can be modified safely"""
    sd_filename: str = Field(default="gg.wp", description="Primary microSD filename")
    sd_filename_wq: str = Field(default="gg.wq", description="microSD dump filename")
    data_period: int = Field(default=250, ge=10, le=4294967295, description="Main data update period (ms)")
    data_period_lnd: int = Field(default=250, ge=10, le=4294967295, description="Post-landing data period (ms)")
    press_buffer_len: int = Field(default=64, ge=8, le=256, description="Pressure buffer size")
    press_land_delta: int = Field(default=20, ge=5, le=100, description="Landing detection pressure delta (Pa)")


class CriticalSettings(BaseModel):
    """Critical settings from user.h - require careful handling"""
    start_th: int = Field(default=60, ge=10, le=200, description="Launch detection threshold (Pa)")
    eject_th: int = Field(default=240, ge=100, le=255, description="Ejection trigger threshold (8-bit)")


class DeviceConfig(BaseModel):
    """Complete device configuration"""
    safe_settings: SafeSettings = SafeSettings()
    critical_settings: CriticalSettings = CriticalSettings()
    lora_config: LoRaConfig = LoRaConfig()

    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    modified_at: datetime = Field(default_factory=datetime.now)
    device_id: Optional[str] = None
    firmware_version: Optional[str] = None


class TelemetryData(BaseModel):
    """Real-time telemetry data structure"""
    timestamp: datetime = Field(default_factory=datetime.now)
    altitude: Optional[float] = Field(None, description="Altitude in meters")
    velocity: Optional[float] = Field(None, description="Velocity in m/s")
    battery_voltage: Optional[float] = Field(None, description="Battery voltage in V")
    rssi: Optional[int] = Field(None, description="RSSI value")
    latitude: Optional[float] = Field(None, description="GPS latitude")
    longitude: Optional[float] = Field(None, description="GPS longitude")
    pressure: Optional[float] = Field(None, description="Pressure in Pa")
    temperature: Optional[float] = Field(None, description="Temperature in °C")
    acceleration_x: Optional[float] = Field(None, description="X-axis acceleration")
    acceleration_y: Optional[float] = Field(None, description="Y-axis acceleration")
    acceleration_z: Optional[float] = Field(None, description="Z-axis acceleration")
    gyro_x: Optional[float] = Field(None, description="X-axis gyroscope")
    gyro_y: Optional[float] = Field(None, description="Y-axis gyroscope")
    gyro_z: Optional[float] = Field(None, description="Z-axis gyroscope")


class DeviceStatus(str, Enum):
    """Device connection status"""
    DISCONNECTED = "disconnected"
    CONNECTED_USB = "connected_usb"
    CONNECTED_LORA = "connected_lora"
    ERROR = "error"


class TestResult(BaseModel):
    """Test execution result"""
    test_name: str
    status: str = Field(description="OK, FAIL, or ERROR")
    message: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class SensorReading(BaseModel):
    """Individual sensor reading for pre-flight test"""
    sensor_name: str
    status: str = Field(description="OK, FAIL, or NO_DATA")
    value: Optional[float] = None
    unit: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ConnectionInfo(BaseModel):
    """Device connection information"""
    status: DeviceStatus
    port: Optional[str] = None
    device_type: Optional[str] = None  # "device" or "lora_link"
    last_seen: Optional[datetime] = None
    signal_strength: Optional[int] = None  # RSSI for LoRa
