#!/usr/bin/env python3
"""
HZ GCH - Ground Control Hub
Главная точка входа в приложение
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import logging

# Добавляем текущую папку в путь для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import AppSettings
from utils.logger import setup_logger
from gui.main_window import MainWindow


def main():
    """Главная функция запуска приложения"""
    try:
        # Настройка логирования
        setup_logger()
        logger = logging.getLogger(__name__)
        logger.info("Запуск HZ GCH Ground Control Hub")

        # Создание директории для пользовательских файлов
        AppSettings.create_user_directory()

        # Создание главного окна
        root = tk.Tk()
        app = MainWindow(root)

        # Запуск главного цикла
        root.mainloop()

    except Exception as e:
        logging.error(f"Критическая ошибка при запуске: {e}")
        messagebox.showerror("Ошибка", f"Не удалось запустить приложение:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()