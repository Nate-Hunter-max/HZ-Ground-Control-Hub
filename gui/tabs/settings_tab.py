"""
Вкладка настроек аппарата
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import logging
from utils.logger import GCHLogger
from config.settings import AppSettings


class SettingsTab(ttk.Frame):
    """Вкладка для настройки параметров аппарата"""

    def __init__(self, parent):
        super().__init__(parent)
        self.logger = GCHLogger(__name__)

        # Словари для хранения настроек
        self.safe_settings = {}
        self.critical_settings = {}
        self.radio_settings = {}

        self._create_widgets()
        self._load_default_settings()

    def _create_widgets(self):
        """Создание виджетов вкладки"""

        # Главный контейнер с прокруткой
        self.canvas = tk.Canvas(self)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Панель управления файлами
        self._create_file_controls()

        # Секция безопасных настроек
        self._create_safe_settings_section()

        # Секция критических настроек
        self._create_critical_settings_section()

        # Секция настроек радио
        self._create_radio_settings_section()

        # Панель управления
        self._create_control_panel()

        # Размещение элементов
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def _create_file_controls(self):
        """Создание панели управления файлами конфигурации"""
        file_frame = ttk.LabelFrame(self.scrollable_frame, text="Управление конфигурацией", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)

        buttons_frame = ttk.Frame(file_frame)
        buttons_frame.pack(fill="x")

        ttk.Button(
            buttons_frame,
            text="Загрузить из файла",
            command=self._load_from_file
        ).pack(side="left", padx=(0, 5))

        ttk.Button(
            buttons_frame,
            text="Сохранить в файл",
            command=self._save_to_file
        ).pack(side="left", padx=5)

        ttk.Button(
            buttons_frame,
            text="Сбросить к умолчанию",
            command=self._reset_to_defaults
        ).pack(side="left", padx=5)

    def _create_safe_settings_section(self):
        """Создание секции безопасных настроек"""
        safe_frame = ttk.LabelFrame(self.scrollable_frame, text="Безопасные настройки", padding=10)
        safe_frame.pack(fill="x", padx=10, pady=5)

        # Создание полей для safe_settings
        settings_data = [
            ("max_altitude", "Максимальная высота (м)", 1000, 0, 5000),
            ("max_speed", "Максимальная скорость (м/с)", 100, 0, 500),
            ("recovery_delay", "Задержка восстановления (с)", 5, 0, 60),
            ("telemetry_interval", "Интервал телеметрии (мс)", 100, 50, 1000),
            ("log_level", "Уровень логирования", 2, 0, 4),
        ]

        self.safe_vars = {}
        for i, (key, label, default, min_val, max_val) in enumerate(settings_data):
            row_frame = ttk.Frame(safe_frame)
            row_frame.pack(fill="x", pady=2)

            ttk.Label(row_frame, text=label, width=25).pack(side="left")

            var = tk.IntVar(value=default)
            self.safe_vars[key] = var

            spinbox = ttk.Spinbox(
                row_frame,
                from_=min_val,
                to=max_val,
                textvariable=var,
                width=10
            )
            spinbox.pack(side="left", padx=5)

            ttk.Label(row_frame, text=f"({min_val}-{max_val})", foreground="gray").pack(side="left", padx=5)

    def _create_critical_settings_section(self):
        """Создание секции критических настроек"""
        critical_frame = ttk.LabelFrame(self.scrollable_frame, text="⚠️ Критические настройки", padding=10)
        critical_frame.pack(fill="x", padx=10, pady=5)

        # Предупреждение
        warning_frame = ttk.Frame(critical_frame)
        warning_frame.pack(fill="x", pady=(0, 10))

        warning_label = ttk.Label(
            warning_frame,
            text="ВНИМАНИЕ: Изменение этих настроек может повлиять на безопасность полета!",
            foreground="red",
            font=("Arial", 9, "bold")
        )
        warning_label.pack()

        # Чекбокс для разблокировки редактирования
        self.critical_unlock_var = tk.BooleanVar()
        unlock_check = ttk.Checkbutton(
            critical_frame,
            text="Разрешить редактирование критических настроек",
            variable=self.critical_unlock_var,
            command=self._toggle_critical_settings
        )
        unlock_check.pack(anchor="w", pady=(0, 10))

        # Создание полей для critical_settings
        critical_data = [
            ("min_recovery_altitude", "Мин. высота раскрытия (м)", 200, 50, 1000),
            ("battery_critical_voltage", "Критическое напряжение АКБ (В)", 6.0, 5.0, 8.0),
            ("max_g_force", "Максимальная перегрузка (g)", 15, 5, 50),
            ("recovery_timeout", "Таймаут восстановления (с)", 30, 5, 120),
        ]

        self.critical_vars = {}
        self.critical_widgets = []

        for key, label, default, min_val, max_val in critical_data:
            row_frame = ttk.Frame(critical_frame)
            row_frame.pack(fill="x", pady=2)

            label_widget = ttk.Label(row_frame, text=label, width=25, state="disabled")
            label_widget.pack(side="left")

            if isinstance(default, float):
                var = tk.DoubleVar(value=default)
                spinbox = ttk.Spinbox(
                    row_frame,
                    from_=min_val,
                    to=max_val,
                    increment=0.1,
                    textvariable=var,
                    width=10,
                    state="disabled"
                )
            else:
                var = tk.IntVar(value=default)
                spinbox = ttk.Spinbox(
                    row_frame,
                    from_=min_val,
                    to=max_val,
                    textvariable=var,
                    width=10,
                    state="disabled"
                )

            self.critical_vars[key] = var
            spinbox.pack(side="left", padx=5)

            range_label = ttk.Label(row_frame, text=f"({min_val}-{max_val})", foreground="gray", state="disabled")
            range_label.pack(side="left", padx=5)

            self.critical_widgets.extend([label_widget, spinbox, range_label])

    def _create_radio_settings_section(self):
        """Создание секции настроек радио"""
        radio_frame = ttk.LabelFrame(self.scrollable_frame, text="Настройки LoRa радио", padding=10)
        radio_frame.pack(fill="x", padx=10, pady=5)

        # Частота
        freq_frame = ttk.Frame(radio_frame)
        freq_frame.pack(fill="x", pady=2)
        ttk.Label(freq_frame, text="Частота (МГц)", width=20).pack(side="left")
        self.freq_var = tk.DoubleVar(value=AppSettings.LORA_DEFAULT_FREQ)
        freq_spinbox = ttk.Spinbox(
            freq_frame,
            from_=433.0,
            to=434.0,
            increment=0.1,
            textvariable=self.freq_var,
            width=10
        )
        freq_spinbox.pack(side="left", padx=5)

        # Spreading Factor
        sf_frame = ttk.Frame(radio_frame)
        sf_frame.pack(fill="x", pady=2)
        ttk.Label(sf_frame, text="Spreading Factor", width=20).pack(side="left")
        self.sf_var = tk.IntVar(value=AppSettings.LORA_DEFAULT_SF)
        sf_combo = ttk.Combobox(
            sf_frame,
            textvariable=self.sf_var,
            values=[7, 8, 9, 10, 11, 12],
            width=8,
            state="readonly"
        )
        sf_combo.pack(side="left", padx=5)

        # Мощность
        power_frame = ttk.Frame(radio_frame)
        power_frame.pack(fill="x", pady=2)
        ttk.Label(power_frame, text="Мощность (дБм)", width=20).pack(side="left")
        self.power_var = tk.IntVar(value=AppSettings.LORA_DEFAULT_POWER)
        power_spinbox = ttk.Spinbox(
            power_frame,
            from_=0,
            to=20,
            textvariable=self.power_var,
            width=10
        )
        power_spinbox.pack(side="left", padx=5)

        # Bandwidth
        bw_frame = ttk.Frame(radio_frame)
        bw_frame.pack(fill="x", pady=2)
        ttk.Label(bw_frame, text="Полоса (кГц)", width=20).pack(side="left")
        self.bw_var = tk.IntVar(value=AppSettings.LORA_DEFAULT_BW)
        bw_combo = ttk.Combobox(
            bw_frame,
            textvariable=self.bw_var,
            values=[62.5, 125, 250, 500],
            width=8,
            state="readonly"
        )
        bw_combo.pack(side="left", padx=5)

    def _create_control_panel(self):
        """Создание панели управления"""
        control_frame = ttk.Frame(self.scrollable_frame)
        control_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(
            control_frame,
            text="Прочитать из устройства",
            command=self._read_from_device
        ).pack(side="left", padx=5)

        ttk.Button(
            control_frame,
            text="Записать в устройство",
            command=self._write_to_device
        ).pack(side="left", padx=5)

        ttk.Button(
            control_frame,
            text="Проверить связь",
            command=self._test_connection
        ).pack(side="left", padx=5)

        # Статус операций
        self.status_var = tk.StringVar(value="Готов к работе")
        self.status_label = ttk.Label(
            control_frame,
            textvariable=self.status_var,
            foreground="blue"
        )
        self.status_label.pack(side="right", padx=10)

    def _load_default_settings(self):
        """Загрузка настроек по умолчанию"""
        # Эта функция вызывается при инициализации
        self.logger.logger.info("Загружены настройки по умолчанию")

    def _toggle_critical_settings(self):
        """Переключение доступности критических настроек"""
        state = "normal" if self.critical_unlock_var.get() else "disabled"

        for widget in self.critical_widgets:
            widget.config(state=state)

        if self.critical_unlock_var.get():
            self.logger.logger.warning("Разблокированы критические настройки")
        else:
            self.logger.logger.info("Заблокированы критические настройки")

    def _load_from_file(self):
        """Загрузка настроек из файла"""
        filename = filedialog.askopenfilename(
            title="Загрузить конфигурацию",
            filetypes=[("GCH Config", "*.gchcfg"), ("All files", "*.*")],
            initialdir=AppSettings.CONFIG_DIR
        )

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                self._apply_config(config)
                self.status_var.set("Конфигурация загружена")
                self.logger.log_file_operation("load config", filename, "success")

            except Exception as e:
                self.logger.log_error("Config load error", str(e))
                messagebox.showerror("Ошибка", f"Не удалось загрузить конфигурацию:\n{e}")

    def _save_to_file(self):
        """Сохранение настроек в файл"""
        filename = filedialog.asksaveasfilename(
            title="Сохранить конфигурацию",
            filetypes=[("GCH Config", "*.gchcfg"), ("All files", "*.*")],
            initialdir=AppSettings.CONFIG_DIR,
            defaultextension=".gchcfg"
        )

        if filename:
            try:
                config = self._get_current_config()

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

                self.status_var.set("Конфигурация сохранена")
                self.logger.log_file_operation("save config", filename, "success")

            except Exception as e:
                self.logger.log_error("Config save error", str(e))
                messagebox.showerror("Ошибка", f"Не удалось сохранить конфигурацию:\n{e}")

    def _reset_to_defaults(self):
        """Сброс к настройкам по умолчанию"""
        if messagebox.askyesno("Подтверждение", "Сбросить все настройки к значениям по умолчанию?"):
            self._load_default_settings()
            self.status_var.set("Настройки сброшены к умолчанию")
            self.logger.logger.info("Настройки сброшены к умолчанию")

    def _apply_config(self, config):
        """Применение конфигурации к виджетам"""
        # TODO: Реализовать применение загруженной конфигурации
        pass

    def _get_current_config(self):
        """Получение текущей конфигурации из виджетов"""
        config = {
            "safe_settings": {key: var.get() for key, var in self.safe_vars.items()},
            "critical_settings": {key: var.get() for key, var in self.critical_vars.items()},
            "radio_settings": {
                "frequency": self.freq_var.get(),
                "spreading_factor": self.sf_var.get(),
                "power": self.power_var.get(),
                "bandwidth": self.bw_var.get()
            }
        }
        return config

    def _read_from_device(self):
        """Чтение настроек из устройства"""
        self.status_var.set("Чтение из устройства...")
        self.logger.logger.info("Запрос чтения настроек из устройства")

        # TODO: Реализовать чтение через USB CDC
        self.after(1000, lambda: self.status_var.set("Настройки прочитаны (заглушка)"))

    def _write_to_device(self):
        """Запись настроек в устройство"""
        config = self._get_current_config()

        if self.critical_unlock_var.get():
            result = messagebox.askyesnocancel(
                "Подтверждение",
                "Вы изменили критические настройки!\n"
                "Это может повлиять на безопасность полета.\n\n"
                "Продолжить запись?"
            )
            if not result:
                return

        self.status_var.set("Запись в устройство...")
        self.logger.logger.info("Запрос записи настроек в устройство")

        # TODO: Реализовать запись через USB CDC
        self.after(1000, lambda: self.status_var.set("Настройки записаны (заглушка)"))

    def _test_connection(self):
        """Проверка связи с устройством"""
        self.status_var.set("Проверка связи...")
        self.logger.logger.info("Проверка связи с устройством")

        # TODO: Реализовать ping через USB CDC
        self.after(1000, lambda: self.status_var.set("Связь установлена (заглушка)"))