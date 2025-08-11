"""
Настройки и конфигурация приложения HZ GCH
"""

import os
from pathlib import Path


class AppSettings:
    """Класс для управления настройками приложения"""

    # Основные настройки приложения
    APP_NAME = "HZ GCH"
    APP_VERSION = "1.0.0"
    MIN_WINDOW_WIDTH = 1366
    MIN_WINDOW_HEIGHT = 768

    # Пути к файлам и папкам
    USER_HOME = Path.home()
    USER_DIR = USER_HOME / "GCH"
    CONFIG_DIR = USER_DIR / "config"
    LOGS_DIR = USER_DIR / "logs"
    DATA_DIR = USER_DIR / "data"

    # Файлы конфигурации
    APP_CONFIG_FILE = CONFIG_DIR / "app_config.json"
    DEVICE_CONFIG_FILE = CONFIG_DIR / "device_config.gchcfg"
    PLOT_CONFIG_FILE = CONFIG_DIR / "plots_config.gchplot"
    APP_LOG_FILE = LOGS_DIR / "gch.log"

    # Настройки COM-портов
    SERIAL_TIMEOUT = 1.0
    SERIAL_BAUDRATE = 115200

    # VID/PID для автопоиска устройств
    DEVICE_VID_PID = {
        "REGULAR_HZ": {"vid": 0x0483, "pid": 0x5740},  # STM32F401
        "LORA_LINK": {"vid": 0x0483, "pid": 0x5741}  # STM32F103
    }

    # Настройки LoRa
    LORA_DEFAULT_FREQ = 433.0
    LORA_DEFAULT_SF = 7
    LORA_DEFAULT_POWER = 14
    LORA_DEFAULT_BW = 125

    # Настройки GUI
    DEFAULT_THEME = "equilux"  # Темная тема по умолчанию
    AVAILABLE_THEMES = ["equilux", "arc", "clearlooks"]

    @classmethod
    def create_user_directory(cls):
        """Создание пользовательских директорий"""
        for directory in [cls.USER_DIR, cls.CONFIG_DIR, cls.LOGS_DIR, cls.DATA_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_default_config(cls):
        """Получение конфигурации по умолчанию"""
        return {
            "theme": cls.DEFAULT_THEME,
            "window": {
                "width": cls.MIN_WINDOW_WIDTH,
                "height": cls.MIN_WINDOW_HEIGHT,
                "maximized": False
            },
            "serial": {
                "timeout": cls.SERIAL_TIMEOUT,
                "baudrate": cls.SERIAL_BAUDRATE
            },
            "lora": {
                "frequency": cls.LORA_DEFAULT_FREQ,
                "spreading_factor": cls.LORA_DEFAULT_SF,
                "power": cls.LORA_DEFAULT_POWER,
                "bandwidth": cls.LORA_DEFAULT_BW
            }
        }