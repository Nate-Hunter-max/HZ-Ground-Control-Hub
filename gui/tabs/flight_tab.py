"""
Вкладка полета в реальном времени
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
import json
from datetime import datetime
from utils.logger import GCHLogger


class FlightTab(ttk.Frame):
    """Вкладка для мониторинга полета в реальном времени"""

    def __init__(self, parent):
        super().__init__(parent)
        self.logger = GCHLogger(__name__)

        # Флаги состояния
        self.is_connected = False
        self.is_recording = False
        self.connection_type = "USB"  # USB или LoRa

        # Данные телеметрии
        self.telemetry_data = {
            "altitude": 0.0,
            "speed": 0.0,
            "battery_voltage": 0.0,
            "rssi": -100,
            "latitude": 0.0,
            "longitude": 0.0,
            "roll": 0.0,
            "pitch": 0.0,
            "yaw": 0.0,
            "timestamp": None
        }

        self._create_widgets()
        self._start_telemetry_thread()

    def _create_widgets(self):
        """Создание виджетов вкладки"""

        # Панель подключения
        self._create_connection_panel()

        # Основная область - разделена на две части
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Левая панель - дашборд
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=2)
        self._create_dashboard(left_frame)

        # Правая панель - координаты и ориентация
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        self._create_position_panel(right_frame)

        # Нижняя панель управления
        self._create_control_panel()

    def _create_connection_panel(self):
        """Создание панели управления подключением"""
        conn_frame = ttk.LabelFrame(self, text="Подключение", padding=5)
        conn_frame.pack(fill="x", padx=5, pady=5)

        # Выбор типа подключения
        type_frame = ttk.Frame(conn_frame)
        type_frame.pack(side="left", padx=5)

        ttk.Label(type_frame, text="Тип:").pack(side="left")
        self.connection_var = tk.StringVar(value="USB")
        conn_combo = ttk.Combobox(
            type_frame,
            textvariable=self.connection_var,
            values=["USB", "LoRa"],
            width=8,
            state="readonly"
        )
        conn_combo.pack(side="left", padx=5)
        conn_combo.bind("<<ComboboxSelected>>", self._on_connection_type_changed)

        # Кнопки управления подключением
        ttk.Button(
            conn_frame,
            text="Подключить",
            command=self._connect_device
        ).pack(side="left", padx=5)

        ttk.Button(
            conn_frame,
            text="Отключить",
            command=self._disconnect_device
        ).pack(side="left", padx=5)

        # Индикатор состояния подключения
        self.connection_status = ttk.Label(
            conn_frame,
            text="Не подключен",
            foreground="red"
        )
        self.connection_status.pack(side="right", padx=10)

    def _create_dashboard(self, parent):
        """Создание числового дашборда"""
        dashboard_frame = ttk.LabelFrame(parent, text="Телеметрия", padding=10)
        dashboard_frame.pack(fill="both", expand=True)

        # Создаем сетку для показателей
        indicators = [
            ("altitude", "Высота", "м", "blue"),
            ("speed", "Скорость", "м/с", "green"),
            ("battery_voltage", "Напряжение АКБ", "В", "orange"),
            ("rssi", "Уровень сигнала", "дБм", "purple")
        ]

        self.indicator_vars = {}
        self.indicator_labels = {}

        for i, (key, name, unit, color) in enumerate(indicators):
            row = i // 2
            col = i % 2

            # Рамка для индикатора
            indicator_frame = ttk.LabelFrame(dashboard_frame, text=name, padding=10)
            indicator_frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")

            # Большое значение
            var = tk.StringVar(value="0.0")
            self.indicator_vars[key] = var

            value_label = ttk.Label(
                indicator_frame,
                textvariable=var,
                font=("Arial", 24, "bold"),
                foreground=color
            )
            value_label.pack()

            # Единицы измерения
            unit_label = ttk.Label(
                indicator_frame,
                text=unit,
                font=("Arial", 12),
                foreground="gray"
            )
            unit_label.pack()

            self.indicator_labels[key] = value_label

        # Настройка растягивания колонок
        dashboard_frame.grid_columnconfigure(0, weight=1)
        dashboard_frame.grid_columnconfigure(1, weight=1)

    def _create_position_panel(self, parent):
        """Создание панели координат и ориентации"""
        # Координаты
        coords_frame = ttk.LabelFrame(parent, text="Координаты", padding=10)
        coords_frame.pack(fill="x", padx=5, pady=5)

        # Широта
        lat_frame = ttk.Frame(coords_frame)
        lat_frame.pack(fill="x", pady=2)
        ttk.Label(lat_frame, text="Широта:", width=12).pack(side="left")
        self.latitude_var = tk.StringVar(value="0.000000")
        ttk.Label(lat_frame, textvariable=self.latitude_var, font=("Courier", 10)).pack(side="left")

        # Долгота
        lon_frame = ttk.Frame(coords_frame)
        lon_frame.pack(fill="x", pady=2)
        ttk.Label(lon_frame, text="Долгота:", width=12).pack(side="left")
        self.longitude_var = tk.StringVar(value="0.000000")
        ttk.Label(lon_frame, textvariable=self.longitude_var, font=("Courier", 10)).pack(side="left")

        # Ориентация
        orientation_frame = ttk.LabelFrame(parent, text="Ориентация", padding=10)
        orientation_frame.pack(fill="x", padx=5, pady=5)

        # Roll
        roll_frame = ttk.Frame(orientation_frame)
        roll_frame.pack(fill="x", pady=2)
        ttk.Label(roll_frame, text="Крен:", width=8).pack(side="left")
        self.roll_var = tk.StringVar(value="0.0°")
        ttk.Label(roll_frame, textvariable=self.roll_var, font=("Courier", 10)).pack(side="left")

        # Pitch
        pitch_frame = ttk.Frame(orientation_frame)
        pitch_frame.pack(fill="x", pady=2)
        ttk.Label(pitch_frame, text="Тангаж:", width=8).pack(side="left")
        self.pitch_var = tk.StringVar(value="0.0°")
        ttk.Label(pitch_frame, textvariable=self.pitch_var, font=("Courier", 10)).pack(side="left")

        # Yaw
        yaw_frame = ttk.Frame(orientation_frame)
        yaw_frame.pack(fill="x", pady=2)
        ttk.Label(yaw_frame, text="Рыскание:", width=8).pack(side="left")
        self.yaw_var = tk.StringVar(value="0.0°")
        ttk.Label(yaw_frame, textvariable=self.yaw_var, font=("Courier", 10)).pack(side="left")

        # Визуальный индикатор ориентации
        self._create_attitude_indicator(parent)

        # Лог событий
        self._create_event_log(parent)

    def _create_attitude_indicator(self, parent):
        """Создание визуального индикатора ориентации"""
        attitude_frame = ttk.LabelFrame(parent, text="Индикатор ориентации", padding=10)
        attitude_frame.pack(fill="x", padx=5, pady=5)

        self.attitude_canvas = tk.Canvas(
            attitude_frame,
            width=150,
            height=150,
            bg="black",
            highlightthickness=1,
            highlightbackground="gray"
        )
        self.attitude_canvas.pack()

        # Рисуем начальное состояние
        self._draw_attitude_indicator()

    def _create_event_log(self, parent):
        """Создание лога событий"""
        log_frame = ttk.LabelFrame(parent, text="События", padding=5)
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Текстовое поле с прокруткой
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill="both", expand=True)

        self.event_text = tk.Text(
            text_frame,
            height=8,
            wrap=tk.WORD,
            font=("Courier", 9)
        )

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.event_text.yview)
        self.event_text.configure(yscrollcommand=scrollbar.set)

        self.event_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Добавляем начальное сообщение
        self._add_event("Система запущена", "INFO")

    def _create_control_panel(self):
        """Создание панели управления"""
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", padx=5, pady=5)

        # Управление записью
        record_frame = ttk.LabelFrame(control_frame, text="Запись лога", padding=5)
        record_frame.pack(side="left", fill="x", expand=True, padx=5)

        self.record_button = ttk.Button(
            record_frame,
            text="Старт записи",
            command=self._toggle_recording
        )
        self.record_button.pack(side="left", padx=5)

        self.record_status = ttk.Label(
            record_frame,
            text="Запись остановлена",
            foreground="red"
        )
        self.record_status.pack(side="left", padx=10)

        # Команды устройству
        command_frame = ttk.LabelFrame(control_frame, text="Команды", padding=5)
        command_frame.pack(side="right", padx=5)

        ttk.Button(
            command_frame,
            text="Пинг",
            command=self._send_ping
        ).pack(side="left", padx=2)

        ttk.Button(
            command_frame,
            text="Сброс",
            command=self._send_reset
        ).pack(side="left", padx=2)

        # Поле для пользовательских команд
        cmd_frame = ttk.Frame(command_frame)
        cmd_frame.pack(side="left", padx=10)

        self.command_entry = ttk.Entry(cmd_frame, width=15)
        self.command_entry.pack(side="left", padx=2)
        self.command_entry.bind("<Return>", self._send_custom_command)

        ttk.Button(
            cmd_frame,
            text="Отправить",
            command=self._send_custom_command
        ).pack(side="left", padx=2)

    def _draw_attitude_indicator(self):
        """Отрисовка индикатора ориентации"""
        self.attitude_canvas.delete("all")

        # Получаем текущие углы
        roll = self.telemetry_data.get("roll", 0.0)
        pitch = self.telemetry_data.get("pitch", 0.0)

        cx, cy = 75, 75  # Центр
        radius = 60

        # Фон (небо/земля)
        self.attitude_canvas.create_oval(
            cx - radius, cy - radius,
            cx + radius, cy + radius,
            fill="lightblue", outline="white", width=2
        )

        # Линия горизонта
        import math
        roll_rad = math.radians(roll)

        # Вычисляем концы линии горизонта
        line_length = radius * 0.8
        x1 = cx - line_length * math.cos(roll_rad)
        y1 = cy + line_length * math.sin(roll_rad)
        x2 = cx + line_length * math.cos(roll_rad)
        y2 = cy - line_length * math.sin(roll_rad)

        self.attitude_canvas.create_line(
            x1, y1, x2, y2,
            fill="white", width=3
        )

        # Центральная точка
        self.attitude_canvas.create_oval(
            cx - 3, cy - 3, cx + 3, cy + 3,
            fill="red", outline="white"
        )

        # Шкала углов
        for angle in [-60, -30, 0, 30, 60]:
            angle_rad = math.radians(angle)
            x = cx + (radius - 10) * math.sin(angle_rad)
            y = cy - (radius - 10) * math.cos(angle_rad)

            self.attitude_canvas.create_text(
                x, y, text=str(angle) + "°",
                fill="white", font=("Arial", 8)
            )

    def _start_telemetry_thread(self):
        """Запуск потока обновления телеметрии"""
        self.telemetry_thread = threading.Thread(target=self._telemetry_loop, daemon=True)
        self.telemetry_thread.start()

    def _telemetry_loop(self):
        """Основной цикл получения телеметрии"""
        while True:
            try:
                if self.is_connected:
                    # Симуляция получения данных
                    self._simulate_telemetry()

                    # Обновляем GUI
                    self.after(0, self._update_telemetry_display)

                time.sleep(0.1)  # 10 Hz обновление

            except Exception as e:
                self.logger.log_error("Telemetry loop error", str(e))
                break

    def _simulate_telemetry(self):
        """Симуляция телеметрии (для тестирования)"""
        import random
        import math

        # Симулируем изменяющиеся данные
        t = time.time() / 10

        self.telemetry_data.update({
            "altitude": 100 + 50 * math.sin(t),
            "speed": 20 + 10 * math.cos(t * 1.5),
            "battery_voltage": 7.4 - 0.1 * math.sin(t * 0.5),
            "rssi": -60 + 10 * math.sin(t * 2),
            "latitude": 55.7558 + 0.001 * math.sin(t * 0.3),
            "longitude": 37.6176 + 0.001 * math.cos(t * 0.3),
            "roll": 15 * math.sin(t * 3),
            "pitch": 10 * math.cos(t * 2),
            "yaw": 45 + 30 * math.sin(t),
            "timestamp": datetime.now()
        })

    def _update_telemetry_display(self):
        """Обновление отображения телеметрии"""
        # Обновляем числовые индикаторы
        self.indicator_vars["altitude"].set(f"{self.telemetry_data['altitude']:.1f}")
        self.indicator_vars["speed"].set(f"{self.telemetry_data['speed']:.1f}")
        self.indicator_vars["battery_voltage"].set(f"{self.telemetry_data['battery_voltage']:.2f}")
        self.indicator_vars["rssi"].set(f"{self.telemetry_data['rssi']:.0f}")

        # Обновляем координаты
        self.latitude_var.set(f"{self.telemetry_data['latitude']:.6f}")
        self.longitude_var.set(f"{self.telemetry_data['longitude']:.6f}")

        # Обновляем ориентацию
        self.roll_var.set(f"{self.telemetry_data['roll']:.1f}°")
        self.pitch_var.set(f"{self.telemetry_data['pitch']:.1f}°")
        self.yaw_var.set(f"{self.telemetry_data['yaw']:.1f}°")

        # Обновляем индикатор ориентации
        self._draw_attitude_indicator()

        # Логируем телеметрию
        if self.is_recording:
            self.logger.log_telemetry(
                self.telemetry_data['timestamp'],
                self.telemetry_data['altitude'],
                self.telemetry_data['speed'],
                self.telemetry_data['battery_voltage'],
                self.telemetry_data['rssi']
            )

    def _add_event(self, message, level="INFO"):
        """Добавление события в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        color_map = {
            "INFO": "blue",
            "WARNING": "orange",
            "ERROR": "red",
            "SUCCESS": "green"
        }

        self.event_text.config(state="normal")
        self.event_text.insert("end", f"[{timestamp}] {message}\n")

        # Прокрутка к концу
        self.event_text.see("end")
        self.event_text.config(state="disabled")

    # Обработчики событий
    def _on_connection_type_changed(self, event=None):
        """Обработчик смены типа подключения"""
        conn_type = self.connection_var.get()
        self._add_event(f"Выбран тип подключения: {conn_type}")

        if self.is_connected:
            self._disconnect_device()

    def _connect_device(self):
        """Подключение к устройству"""
        conn_type = self.connection_var.get()
        self._add_event(f"Подключение через {conn_type}...")

        # TODO: Реализовать реальное подключение
        self.after(1000, self._on_connection_success)

    def _on_connection_success(self):
        """Обработчик успешного подключения"""
        self.is_connected = True
        self.connection_status.config(text="Подключен", foreground="green")
        self._add_event("Подключение установлено", "SUCCESS")

        # Запускаем симуляцию
        if not hasattr(self, 'telemetry_thread') or not self.telemetry_thread.is_alive():
            self._start_telemetry_thread()

    def _disconnect_device(self):
        """Отключение от устройства"""
        self.is_connected = False
        self.connection_status.config(text="Не подключен", foreground="red")
        self._add_event("Подключение разорвано", "WARNING")

        if self.is_recording:
            self._toggle_recording()

    def _toggle_recording(self):
        """Переключение записи лога"""
        if not self.is_connected:
            self._add_event("Нет подключения к устройству", "ERROR")
            return

        self.is_recording = not self.is_recording

        if self.is_recording:
            self.record_button.config(text="Стоп записи")
            self.record_status.config(text="Идет запись", foreground="green")
            self._add_event("Запись лога начата", "SUCCESS")
        else:
            self.record_button.config(text="Старт записи")
            self.record_status.config(text="Запись остановлена", foreground="red")
            self._add_event("Запись лога остановлена", "INFO")

    def _send_ping(self):
        """Отправка ping команды"""
        if not self.is_connected:
            self._add_event("Нет подключения к устройству", "ERROR")
            return

        self._add_event("Отправка ping...")
        self.logger.log_command_sent("device", "ping")

        # Симуляция ответа
        self.after(500, lambda: self._add_event("Pong получен", "SUCCESS"))

    def _send_reset(self):
        """Отправка команды сброса"""
        if not self.is_connected:
            self._add_event("Нет подключения к устройству", "ERROR")
            return

        result = tk.messagebox.askyesno(
            "Подтверждение",
            "Вы уверены, что хотите перезагрузить устройство?"
        )

        if result:
            self._add_event("Отправка команды сброса...", "WARNING")
            self.logger.log_command_sent("device", "reset")

    def _send_custom_command(self, event=None):
        """Отправка пользовательской команды"""
        command = self.command_entry.get().strip()
        if not command:
            return

        if not self.is_connected:
            self._add_event("Нет подключения к устройству", "ERROR")
            return

        self._add_event(f"Отправка команды: {command}")
        self.logger.log_command_sent("device", command)
        self.command_entry.delete(0, "end")