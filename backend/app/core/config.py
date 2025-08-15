"""
Configuration settings for Ground Control Hub
"""

from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List


class Settings(BaseSettings):
    """Application settings"""

    # Application info
    app_name: str = "Ground Control Hub"
    version: str = "0.1.0"

    # Server settings
    host: str = "127.0.0.1"
    port: int = 8000

    # File paths
    gch_directory: Path = Path.home() / "GCH"
    log_file: str = "gch.log"

    # Serial communication
    serial_timeout: float = 1.0
    serial_baudrate: int = 115200

    # LoRa Link settings
    lora_vid: str = "0483"  # STM32F103 VID
    lora_pid: str = "5740"  # STM32F103 PID

    # Device settings
    device_vid: str = "0483"  # STM32F401 VID
    device_pid: str = "5740"  # STM32F401 PID

    # Telemetry settings
    telemetry_buffer_size: int = 1000
    telemetry_update_interval: float = 0.25  # 250ms as per DATA_PERIOD

    # File formats
    supported_log_formats: List[str] = [".log", ".csv", ".bin"]
    config_extension: str = ".gchcfg"
    plot_extension: str = ".gchplot"

    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings()