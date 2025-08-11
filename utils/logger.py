"""
Модуль логирования для HZ GCH
"""

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from config.settings import AppSettings


def setup_logger():
    """Настройка системы логирования"""

    # Создаем директорию для логов если она не существует
    AppSettings.LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Настройка форматирования
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Создание основного логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Удаляем существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Обработчик для файла с ротацией по дате
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=AppSettings.APP_LOG_FILE,
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Создаем отдельный логгер для GUI событий
    gui_logger = logging.getLogger('gui')
    gui_handler = logging.FileHandler(
        AppSettings.LOGS_DIR / 'gui.log',
        encoding='utf-8'
    )
    gui_handler.setLevel(logging.DEBUG)
    gui_handler.setFormatter(formatter)
    gui_logger.addHandler(gui_handler)

    # Создаем отдельный логгер для коммуникации
    comm_logger = logging.getLogger('communication')
    comm_handler = logging.FileHandler(
        AppSettings.LOGS_DIR / 'communication.log',
        encoding='utf-8'
    )
    comm_handler.setLevel(logging.DEBUG)
    comm_handler.setFormatter(formatter)
    comm_logger.addHandler(comm_handler)

    logging.info("Система логирования инициализирована")


class GCHLogger:
    """Вспомогательный класс для логирования специфичных для приложения событий"""

    def __init__(self, name):
        self.logger = logging.getLogger(name)

    def log_device_connection(self, device_type, port, status):
        """Логирование подключения устройств"""
        self.logger.info(f"Device connection: {device_type} on {port} - {status}")

    def log_command_sent(self, device, command):
        """Логирование отправленных команд"""
        self.logger.debug(f"Command sent to {device}: {command}")

    def log_data_received(self, device, data_type, size):
        """Логирование получения данных"""
        self.logger.debug(f"Data received from {device}: {data_type} ({size} bytes)")

    def log_file_operation(self, operation, filename, status):
        """Логирование файловых операций"""
        self.logger.info(f"File {operation}: {filename} - {status}")

    def log_test_result(self, test_name, result, details=""):
        """Логирование результатов тестов"""
        self.logger.info(f"Test '{test_name}': {result} {details}")

    def log_error(self, error_type, details):
        """Логирование ошибок"""
        self.logger.error(f"{error_type}: {details}")

    def log_telemetry(self, timestamp, altitude, speed, battery, rssi):
        """Логирование телеметрии (только в файл, не в консоль)"""
        telemetry_logger = logging.getLogger('telemetry')
        if not telemetry_logger.handlers:
            handler = logging.FileHandler(
                AppSettings.LOGS_DIR / 'telemetry.log',
                encoding='utf-8'
            )
            formatter = logging.Formatter('%(asctime)s,%(message)s')
            handler.setFormatter(formatter)
            telemetry_logger.addHandler(handler)
            telemetry_logger.setLevel(logging.INFO)
            telemetry_logger.propagate = False

        telemetry_logger.info(f"{timestamp},{altitude},{speed},{battery},{rssi}")