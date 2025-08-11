"""
Главное окно приложения HZ GCH
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import logging
from ttkthemes import ThemedTk

from config.settings import AppSettings
from gui.widgets.status_bar import StatusBar
from gui.tabs.settings_tab import SettingsTab
from gui.tabs.flight_tab import FlightTab
from gui.tabs.tests_tab import TestsTab
from gui.tabs.lora_tab import LoRaTab
from gui.tabs.analysis_tab import AnalysisTab
from utils.logger import GCHLogger

class MainWindow:
    """Главное окно приложения"""

    def __init__(self, root):
        self.root = root
        self.logger = GCHLogger(__name__)
        self.config = self._load_config()

        # Настройка главного окна
        self._setup_window()

        # Создание GUI элементов
        self._create_menu()
        self._create_notebook()
        self._create_status_bar()

        # Инициализация вкладок
        self._init_tabs()

        # Обработчики событий
        self._bind_events()

        self.logger.logger.info("Главное окно инициализировано")

    def _load_config(self):
        """Загрузка конфигурации приложения"""
        try:
            if AppSettings.APP_CONFIG_FILE.exists():
                with open(AppSettings.APP_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.logger.log_file_operation("load", AppSettings.APP_CONFIG_FILE, "success")
                    return config
        except Exception as e:
            self.logger.log_error("Config load error", str(e))

        # Возвращаем конфигурацию по умолчанию
        return AppSettings.get_default_config()

    def _save_config(self):
        """Сохранение конфигурации приложения"""
        try:
            # Обновляем текущие размеры окна
            self.config["window"]["width"] = self.root.winfo_width()
            self.config["window"]["height"] = self.root.winfo_height()
            self.config["window"]["maximized"] = bool(self.root.state() == "zoomed")

            with open(AppSettings.APP_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
                self.logger.log_file_operation("save", AppSettings.APP_CONFIG_FILE, "success")
        except Exception as e:
            self.logger.log_error("Config save error", str(e))

    def _setup_window(self):
        """Настройка главного окна"""
        # Установка темы
        if hasattr(self.root, 'set_theme'):
            try:
                self.root.set_theme(self.config.get("theme", AppSettings.DEFAULT_THEME))
            except Exception as e:
                self.logger.log_error("Theme setup error", str(e))

        # Настройка заголовка и иконки
        self.root.title(f"{AppSettings.APP_NAME} v{AppSettings.APP_VERSION}")

        # Размеры окна
        width = self.config["window"].get("width", AppSettings.MIN_WINDOW_WIDTH)
        height = self.config["window"].get("height", AppSettings.MIN_WINDOW_HEIGHT)

        # Центрирование окна
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2

        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(AppSettings.MIN_WINDOW_WIDTH, AppSettings.MIN_WINDOW_HEIGHT)

        # Максимизация окна если была включена
        if self.config["window"].get("maximized", False):
            self.root.state("zoomed")

    def _create_menu(self):
        """Создание главного меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Новый проект", command=self._new_project)
        file_menu.add_command(label="Открыть проект", command=self._open_project)
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт данных", command=self._export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self._on_closing)

        # Меню "Устройства"
        devices_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Устройства", menu=devices_menu)
        devices_menu.add_command(label="Поиск устройств", command=self._scan_devices)
        devices_menu.add_command(label="Отключить все", command=self._disconnect_all)

        # Меню "Вид"
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Вид", menu=view_menu)

        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Тема", menu=theme_menu)

        for theme in AppSettings.AVAILABLE_THEMES:
            theme_menu.add_command(
                label=theme.capitalize(),
                command=lambda t=theme: self._change_theme(t)
            )

        # Меню "Справка"
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self._about)
        help_menu.add_command(label="Руководство", command=self._show_manual)

    def _create_notebook(self):
        """Создание основного интерфейса с вкладками"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _create_status_bar(self):
        """Создание строки состояния"""
        self.status_bar = StatusBar(self.root)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _init_tabs(self):
        """Инициализация всех вкладок"""
        self.tabs = {}

        # Вкладка настроек
        self.tabs["settings"] = SettingsTab(self.notebook)
        self.notebook.add(self.tabs["settings"], text="Настройки")

        # Вкладка полета
        self.tabs["flight"] = FlightTab(self.notebook)
        self.notebook.add(self.tabs["flight"], text="Полёт")

        # Вкладка тестов
        self.tabs["tests"] = TestsTab(self.notebook)
        self.notebook.add(self.tabs["tests"], text="Тесты")

        # Вкладка LoRa Link
        self.tabs["lora"] = LoRaTab(self.notebook)
        self.notebook.add(self.tabs["lora"], text="LoRa Link")

        # Вкладка анализа
        self.tabs["analysis"] = AnalysisTab(self.notebook)
        self.notebook.add(self.tabs["analysis"], text="Анализ")

    def _bind_events(self):
        """Привязка обработчиков событий"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.root.bind("<Control-q>", lambda e: self._on_closing())
        self.root.bind("<F5>", lambda e: self._scan_devices())

    # Обработчики меню
    def _new_project(self):
        """Создание нового проекта"""
        self.logger.logger.info("Создание нового проекта")
        messagebox.showinfo("Информация", "Функция в разработке")

    def _open_project(self):
        """Открытие проекта"""
        self.logger.logger.info("Открытие проекта")
        messagebox.showinfo("Информация", "Функция в разработке")

    def _export_data(self):
        """Экспорт данных"""
        self.logger.logger.info("Экспорт данных")
        messagebox.showinfo("Информация", "Функция в разработке")

    def _scan_devices(self):
        """Поиск устройств"""
        self.logger.logger.info("Поиск устройств")
        self.status_bar.set_message("Поиск устройств...")
        # TODO: Реализовать поиск устройств
        self.status_bar.set_message("Готов")

    def _disconnect_all(self):
        """Отключение всех устройств"""
        self.logger.logger.info("Отключение всех устройств")
        messagebox.showinfo("Информация", "Все устройства отключены")

    def _change_theme(self, theme):
        """Смена темы интерфейса"""
        try:
            if hasattr(self.root, 'set_theme'):
                self.root.set_theme(theme)
                self.config["theme"] = theme
                self._save_config()
                self.logger.logger.info(f"Тема изменена на: {theme}")
        except Exception as e:
            self.logger.log_error("Theme change error", str(e))
            messagebox.showerror("Ошибка", f"Не удалось изменить тему: {e}")

    def _about(self):
        """Показать информацию о программе"""
        about_text = f"""
{AppSettings.APP_NAME} v{AppSettings.APP_VERSION}

Ground Control Hub для управления аппаратом Regular-HZ FDR

Разработано для:
- Настройки параметров аппарата
- Приёма телеметрии в реальном времени  
- Анализа логов полёта
- Проведения тестов
- Управления LoRa Link

© 2024
        """
        messagebox.showinfo("О программе", about_text.strip())

    def _show_manual(self):
        """Показать руководство пользователя"""
        messagebox.showinfo("Руководство", "Руководство пользователя в разработке")

    def _on_closing(self):
        """Обработчик закрытия приложения"""
        try:
            self._save_config()
            self.logger.logger.info("Завершение работы приложения")
            self.root.destroy()
        except Exception as e:
            self.logger.log_error("Shutdown error", str(e))
            self.root.destroy()