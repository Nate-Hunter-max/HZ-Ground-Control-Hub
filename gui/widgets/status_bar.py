"""
Строка состояния для главного окна
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from datetime import datetime


class StatusBar(ttk.Frame):
    """Строка состояния приложения"""

    def __init__(self, parent):
        super().__init__(parent)

        self.device_status = "Не подключен"
        self.battery_level = 0
        self.rssi_level = -100
        self.current_message = "Готов"

        self._create_widgets()
        self._start_update_thread()

    def _create_widgets(self):
        """Создание виджетов строки состояния"""

        # Разделители и отступы
        separator_style = {"relief": tk.SUNKEN, "width": 2}

        # Общее сообщение (слева)
        self.message_label = ttk.Label(
            self,
            text=self.current_message,
            anchor=tk.W,
            width=30
        )
        self.message_label.pack(side=tk.LEFT, padx=(5, 10), pady=2)

        # Разделитель
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=2)

        # Статус подключения устройства
        self.device_frame = ttk.Frame(self)
        self.device_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(self.device_frame, text="Устройство:").pack(side=tk.LEFT)
        self.device_label = ttk.Label(
            self.device_frame,
            text=self.device_status,
            foreground="red"
        )
        self.device_label.pack(side=tk.LEFT, padx=(5, 0))

        # Разделитель
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=2)

        # Уровень заряда батареи
        self.battery_frame = ttk.Frame(self)
        self.battery_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(self.battery_frame, text="АКБ:").pack(side=tk.LEFT)
        self.battery_label = ttk.Label(
            self.battery_frame,
            text=f"{self.battery_level}%"
        )
        self.battery_label.pack(side=tk.LEFT, padx=(5, 0))

        # Прогресс-бар для батареи
        self.battery_progress = ttk.Progressbar(
            self.battery_frame,
            length=50,
            mode='determinate'
        )
        self.battery_progress.pack(side=tk.LEFT, padx=(5, 0))
        self.battery_progress['value'] = self.battery_level

        # Разделитель
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=2)

        # Уровень сигнала RSSI
        self.rssi_frame = ttk.Frame(self)
        self.rssi_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(self.rssi_frame, text="RSSI:").pack(side=tk.LEFT)
        self.rssi_label = ttk.Label(
            self.rssi_frame,
            text=f"{self.rssi_level} dBm"
        )
        self.rssi_label.pack(side=tk.LEFT, padx=(5, 0))

        # Индикатор качества сигнала
        self.signal_canvas = tk.Canvas(
            self.rssi_frame,
            width=60,
            height=20,
            highlightthickness=0
        )
        self.signal_canvas.pack(side=tk.LEFT, padx=(5, 0))
        self._draw_signal_bars()

        # Разделитель
        ttk.Separator(self, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=2)

        # Текущее время (справа)
        self.time_label = ttk.Label(
            self,
            text=datetime.now().strftime("%H:%M:%S"),
            anchor=tk.E,
            width=10
        )
        self.time_label.pack(side=tk.RIGHT, padx=(10, 5), pady=2)

    def _draw_signal_bars(self):
        """Отрисовка индикатора уровня сигнала"""
        self.signal_canvas.delete("all")

        # Определяем количество активных полосок на основе RSSI
        bars_count = self._rssi_to_bars(self.rssi_level)

        bar_width = 8
        bar_spacing = 2
        max_height = 16

        colors = ["red", "orange", "yellow", "lightgreen", "green"]

        for i in range(5):
            x1 = i * (bar_width + bar_spacing) + 5
            y1 = 18 - (i + 1) * 3  # Высота каждой полоски увеличивается
            x2 = x1 + bar_width
            y2 = 18

            if i < bars_count:
                color = colors[min(i, len(colors) - 1)]
            else:
                color = "gray"

            self.signal_canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=color,
                outline="black"
            )

    def _rssi_to_bars(self, rssi):
        """Конвертация RSSI в количество полосок сигнала"""
        if rssi >= -50:
            return 5
        elif rssi >= -60:
            return 4
        elif rssi >= -70:
            return 3
        elif rssi >= -80:
            return 2
        elif rssi >= -90:
            return 1
        else:
            return 0

    def _start_update_thread(self):
        """Запуск потока для обновления времени"""
        self.update_thread = threading.Thread(target=self._update_time, daemon=True)
        self.update_thread.start()

    def _update_time(self):
        """Обновление времени в отдельном потоке"""
        while True:
            try:
                current_time = datetime.now().strftime("%H:%M:%S")
                self.after(0, lambda: self.time_label.config(text=current_time))
                time.sleep(1)
            except Exception:
                break

    def set_message(self, message):
        """Установка общего сообщения"""
        self.current_message = message
        self.message_label.config(text=message)

    def set_device_status(self, status, connected=False):
        """Установка статуса подключения устройства"""
        self.device_status = status
        color = "green" if connected else "red"
        self.device_label.config(text=status, foreground=color)

    def set_battery_level(self, level):
        """Установка уровня заряда батареи (0-100)"""
        self.battery_level = max(0, min(100, level))
        self.battery_label.config(text=f"{self.battery_level}%")
        self.battery_progress['value'] = self.battery_level

        # Изменяем цвет в зависимости от уровня заряда
        if self.battery_level < 20:
            color = "red"
        elif self.battery_level < 50:
            color = "orange"
        else:
            color = "green"

        self.battery_label.config(foreground=color)

    def set_rssi_level(self, rssi):
        """Установка уровня сигнала RSSI"""
        self.rssi_level = rssi
        self.rssi_label.config(text=f"{rssi} dBm")
        self._draw_signal_bars()

        # Изменяем цвет текста в зависимости от уровня сигнала
        bars = self._rssi_to_bars(rssi)
        if bars >= 4:
            color = "green"
        elif bars >= 2:
            color = "orange"
        else:
            color = "red"

        self.rssi_label.config(foreground=color)

    def update_telemetry(self, battery=None, rssi=None):
        """Обновление телеметрических данных"""
        if battery is not None:
            self.set_battery_level(battery)

        if rssi is not None:
            self.set_rssi_level(rssi)