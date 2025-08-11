"""
Вкладка управления LoRa Link
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
import serial.tools.list_ports
import threading
import time
from datetime import datetime
from utils.logger import GCHLogger
from config.settings import AppSettings


class LoRaTab(ttk.Frame):
    """Вкладка для работы с LoRa Link"""

    def __init__(self, parent):
        super().__init__(parent)
        self.logger = GCHLogger(__name__)

        # Состояние подключения
        self.serial_connection = None
        self.is_connected = False
        self.auto_scan_enabled = True
        self.current_port = None

        self._create_widgets()
        self._start_port_scanner()

    def _create_widgets(self):
        """Создание виджетов вкладки"""

        # Панель подключения
        self._create_connection_panel()

        # Основная область - разделена на части
        main_paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Верхняя панель - терминал
        terminal_frame = ttk.LabelFrame(main_paned, text="Терминал LoRa Link", padding=5)
        main_paned.add(terminal_frame, weight=2)
        self._create_terminal(terminal_frame)

        # Нижняя панель - управление и настройки
        control_paned = ttk.PanedWindow(main_paned, orient=tk.HORIZONTAL)
        main_paned.add(control_paned, weight=1)

        # Панель команд
        commands_frame = ttk.LabelFrame(control_paned, text="Команды", padding=5)
        control_paned.add(commands_frame, weight=1)
        self._create_commands_panel(commands_frame)

        # Панель настроек
        settings_frame = ttk.LabelFrame(control_paned, text="Настройки LoRa", padding=5)
        control_paned.add(settings_frame, weight=1)
        self._create_settings_panel(settings_frame)

    def _create_connection_panel(self):
        """Создание панели управления подключением"""
        conn_frame = ttk.LabelFrame(self, text="Подключение к LoRa Link", padding=5)
        conn_frame.pack(fill="x", padx=5, pady=5)

        # Левая часть - выбор порта
        left_frame = ttk.Frame(conn_frame)
        left_frame.pack(side="left", fill="x", expand=True)

        port_frame = ttk.Frame(left_frame)
        port_frame.pack(fill="x")

        ttk.Label(port_frame, text="COM-порт:").pack(side="left")

        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(
            port_frame,
            textvariable=self.port_var,
            width=15,
            state="readonly"
        )
        self.port_combo.pack(side="left", padx=5)

        ttk.Button(
            port_frame,
            text="Обновить",
            command=self._scan_ports
        ).pack(side="left", padx=2)

        # Автопоиск
        self.auto_scan_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            left_frame,
            text="Автопоиск по VID/PID",
            variable=self.auto_scan_var
        ).pack(anchor="w", pady=2)

        # Правая часть - управление подключением
        right_frame = ttk.Frame(conn_frame)
        right_frame.pack(side="right")

        self.connect_button = ttk.Button(
            right_frame,
            text="Подключить",
            command=self._toggle_connection
        )
        self.connect_button.pack(side="left", padx=5)

        # Индикатор состояния
        self.connection_status = ttk.Label(
            right_frame,
            text="Не подключен",
            foreground="red"
        )
        self.connection_status.pack(side="left", padx=10)

    def _create_terminal(self, parent):
        """Создание терминала"""
        # Область вывода
        output_frame = ttk.Frame(parent)
        output_frame.pack(fill="both", expand=True, pady=(0, 5))

        self.terminal_text = tk.Text(
            output_frame,
            height=15,
            wrap=tk.WORD,
            font=("Courier", 9),
            bg="black",
            fg="green",
            state="disabled"
        )

        terminal_scroll = ttk.Scrollbar(output_frame, orient="vertical", command=self.terminal_text.yview)
        self.terminal_text.configure(yscrollcommand=terminal_scroll.set)

        self.terminal_text.pack(side="left", fill="both", expand=True)
        terminal_scroll.pack(side="right", fill="y")

        # Область ввода
        input_frame = ttk.Frame(parent)
        input_frame.pack(fill="x")

        ttk.Label(input_frame, text="Команда:").pack(side="left")

        self.command_entry = ttk.Entry(input_frame)
        self.command_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.command_entry.bind("<Return>", self._send_command)

        ttk.Button(
            input_frame,
            text="Отправить",
            command=self._send_command
        ).pack(side="left")

        ttk.Button(
            input_frame,
            text="Очистить",
            command=self._clear_terminal
        ).pack(side="left", padx=2)

        # Добавляем приветствие
        self._add_terminal_line("LoRa Link Terminal готов к работе", "INFO")

    def _create_commands_panel(self, parent):
        """Создание панели команд"""

        # Основные команды
        basic_frame = ttk.LabelFrame(parent, text="Основные команды", padding=5)
        basic_frame.pack(fill="x", pady=5)

        commands_grid = [
            ("Ping", self._ping_device),
            ("Статус", self._get_status),
            ("Сброс", self._reset_device),
            ("Версия", self._get_version)
        ]

        for i, (text, command) in enumerate(commands_grid):
            row = i // 2
            col = i % 2
            ttk.Button(
                basic_frame,
                text=text,
                command=command,
                width=12
            ).grid(row=row, column=col, padx=2, pady=2, sticky="ew")

        basic_frame.grid_columnconfigure(0, weight=1)
        basic_frame.grid_columnconfigure(1, weight=1)

        # Специальные функции
        special_frame = ttk.LabelFrame(parent, text="Специальные функции", padding=5)
        special_frame.pack(fill="x", pady=5)

        ttk.Button(
            special_frame,
            text="Bind Satellite",
            command=self._bind_satellite
        ).pack(fill="x", pady=2)

        ttk.Button(
            special_frame,
            text="Считать блэкбокс",
            command=self._read_blackbox
        ).pack(fill="x", pady=2)

        ttk.Button(
            special_frame,
            text="Загрузить прошивку",
            command=self._upload_firmware
        ).pack(fill="x", pady=2)

        # Лог файлов
        files_frame = ttk.LabelFrame(parent, text="Файлы", padding=5)
        files_frame.pack(fill="both", expand=True, pady=5)

        ttk.Button(
            files_frame,
            text="Сохранить лог в файл",
            command=self._save_log
        ).pack(fill="x", pady=2)

        ttk.Button(
            files_frame,
            text="Загрузить команды",
            command=self._load_commands
        ).pack(fill="x", pady=2)

    def _create_settings_panel(self, parent):
        """Создание панели настроек LoRa"""

        # Радио параметры
        radio_frame = ttk.LabelFrame(parent, text="Радио параметры", padding=5)
        radio_frame.pack(fill="x", pady=5)

        # Частота
        freq_frame = ttk.Frame(radio_frame)
        freq_frame.pack(fill="x", pady=2)
        ttk.Label(freq_frame, text="Частота (МГц):", width=15).pack(side="left")
        self.lora_freq_var = tk.DoubleVar(value=AppSettings.LORA_DEFAULT_FREQ)
        freq_spinbox = ttk.Spinbox(
            freq_frame,
            from_=433.0,
            to=434.0,
            increment=0.1,
            textvariable=self.lora_freq_var,
            width=10
        )
        freq_spinbox.pack(side="left", padx=5)

        # Адрес
        addr_frame = ttk.Frame(radio_frame)
        addr_frame.pack(fill="x", pady=2)
        ttk.Label(addr_frame, text="Адрес:", width=15).pack(side="left")
        self.lora_addr_var = tk.StringVar(value="0x1234")
        ttk.Entry(
            addr_frame,
            textvariable=self.lora_addr_var,
            width=10
        ).pack(side="left", padx=5)

        # Ключ шифрования
        key_frame = ttk.Frame(radio_frame)
        key_frame.pack(fill="x", pady=2)
        ttk.Label(key_frame, text="Ключ:", width=15).pack(side="left")
        self.lora_key_var = tk.StringVar(value="DefaultKey123")
        ttk.Entry(
            key_frame,
            textvariable=self.lora_key_var,
            width=15,
            show="*"
        ).pack(side="left", padx=5)

        # Кнопки управления настройками
        settings_buttons = ttk.Frame(radio_frame)
        settings_buttons.pack(fill="x", pady=5)

        ttk.Button(
            settings_buttons,
            text="Прочитать",
            command=self._read_lora_settings
        ).pack(side="left", padx=2)

        ttk.Button(
            settings_buttons,
            text="Записать",
            command=self._write_lora_settings
        ).pack(side="left", padx=2)

        # Мониторинг
        monitor_frame = ttk.LabelFrame(parent, text="Мониторинг", padding=5)
        monitor_frame.pack(fill="both", expand=True, pady=5)

        # RSSI
        rssi_frame = ttk.Frame(monitor_frame)
        rssi_frame.pack(fill="x", pady=2)
        ttk.Label(rssi_frame, text="RSSI:", width=10).pack(side="left")
        self.rssi_var = tk.StringVar(value="-100 dBm")
        ttk.Label(rssi_frame, textvariable=self.rssi_var, foreground="blue").pack(side="left")

        # Пакеты
        packets_frame = ttk.Frame(monitor_frame)
        packets_frame.pack(fill="x", pady=2)
        ttk.Label(packets_frame, text="Пакетов:", width=10).pack(side="left")
        self.packets_var = tk.StringVar(value="RX: 0 / TX: 0")
        ttk.Label(packets_frame, textvariable=self.packets_var, foreground="green").pack(side="left")

        # Ошибки
        errors_frame = ttk.Frame(monitor_frame)
        errors_frame.pack(fill="x", pady=2)
        ttk.Label(errors_frame, text="Ошибки:", width=10).pack(side="left")
        self.errors_var = tk.StringVar(value="0")
        ttk.Label(errors_frame, textvariable=self.errors_var, foreground="red").pack(side="left")

        # Автообновление статистики
        self.auto_monitor_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            monitor_frame,
            text="Автообновление",
            variable=self.auto_monitor_var
        ).pack(anchor="w", pady=5)

    def _start_port_scanner(self):
        """Запуск сканера портов"""

        def scanner():
            while True:
                try:
                    if self.auto_scan_var.get() and not self.is_connected:
                        self._scan_ports()
                    time.sleep(2)  # Сканируем каждые 2 секунды
                except Exception:
                    break

        scanner_thread = threading.Thread(target=scanner, daemon=True)
        scanner_thread.start()

    def _scan_ports(self):
        """Сканирование доступных COM-портов"""
        try:
            ports = serial.tools.list_ports.comports()
            available_ports = []
            lora_port = None

            for port in ports:
                port_name = port.device
                available_ports.append(f"{port_name} - {port.description}")

                # Проверяем VID/PID для LoRa Link
                if (hasattr(port, 'vid') and hasattr(port, 'pid') and
                        port.vid == AppSettings.DEVICE_VID_PID["LORA_LINK"]["vid"] and
                        port.pid == AppSettings.DEVICE_VID_PID["LORA_LINK"]["pid"]):
                    lora_port = port_name

            # Обновляем список портов
            self.port_combo['values'] = available_ports

            # Автовыбор LoRa Link порта
            if lora_port and self.auto_scan_var.get():
                for i, port_desc in enumerate(available_ports):
                    if lora_port in port_desc:
                        self.port_combo.current(i)
                        if not self.is_connected:
                            self._add_terminal_line(f"Обнаружен LoRa Link на порту {lora_port}", "INFO")
                        break

        except Exception as e:
            self.logger.log_error("Port scan error", str(e))

    def _toggle_connection(self):
        """Переключение подключения"""
        if self.is_connected:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        """Подключение к LoRa Link"""
        selected = self.port_var.get()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите COM-порт")
            return

        # Извлекаем имя порта
        port_name = selected.split(" - ")[0]

        try:
            self.serial_connection = serial.Serial(
                port=port_name,
                baudrate=AppSettings.SERIAL_BAUDRATE,
                timeout=AppSettings.SERIAL_TIMEOUT
            )

            self.is_connected = True
            self.current_port = port_name
            self.connect_button.config(text="Отключить")
            self.connection_status.config(text=f"Подключен к {port_name}", foreground="green")

            self._add_terminal_line(f"Подключение к {port_name} установлено", "SUCCESS")
            self.logger.log_device_connection("LoRa Link", port_name, "connected")

            # Запускаем поток чтения данных
            self._start_read_thread()

            # Запрашиваем статус
            self._send_raw_command("AT+STATUS")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подключиться к {port_name}:\n{e}")
            self.logger.log_error("LoRa connection error", str(e))

    def _disconnect(self):
        """Отключение от LoRa Link"""
        try:
            if self.serial_connection:
                self.serial_connection.close()
                self.serial_connection = None

            self.is_connected = False
            self.current_port = None
            self.connect_button.config(text="Подключить")
            self.connection_status.config(text="Не подключен", foreground="red")

            self._add_terminal_line("Подключение разорвано", "WARNING")
            self.logger.log_device_connection("LoRa Link", "unknown", "disconnected")

        except Exception as e:
            self.logger.log_error("LoRa disconnect error", str(e))

    def _start_read_thread(self):
        """Запуск потока чтения данных"""

        def reader():
            while self.is_connected and self.serial_connection:
                try:
                    if self.serial_connection.in_waiting > 0:
                        data = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                        if data:
                            self.after(0, lambda d=data: self._add_terminal_line(f"← {d}", "RECEIVED"))
                    time.sleep(0.1)
                except Exception as e:
                    if self.is_connected:  # Только если не преднамеренное отключение
                        self.after(0, lambda: self._add_terminal_line(f"Ошибка чтения: {e}", "ERROR"))
                    break

        read_thread = threading.Thread(target=reader, daemon=True)
        read_thread.start()

    def _add_terminal_line(self, text, msg_type="INFO"):
        """Добавление строки в терминал"""
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Цветовая схема
        colors = {
            "INFO": "lightblue",
            "SUCCESS": "lightgreen",
            "WARNING": "yellow",
            "ERROR": "red",
            "SENT": "cyan",
            "RECEIVED": "white"
        }

        self.terminal_text.config(state="normal")

        # Добавляем строку с цветом
        start_pos = self.terminal_text.index("end-1c")
        self.terminal_text.insert("end", f"[{timestamp}] {text}\n")
        end_pos = self.terminal_text.index("end-1c")

        # Применяем цвет
        color = colors.get(msg_type, "white")
        self.terminal_text.tag_add(msg_type, start_pos, end_pos)
        self.terminal_text.tag_config(msg_type, foreground=color)

        # Прокрутка к концу
        self.terminal_text.see("end")
        self.terminal_text.config(state="disabled")

        # Ограничиваем количество строк (последние 1000)
        lines = self.terminal_text.get("1.0", "end").count('\n')
        if lines > 1000:
            self.terminal_text.config(state="normal")
            self.terminal_text.delete("1.0", "100.0")
            self.terminal_text.config(state="disabled")

    def _send_command(self, event=None):
        """Отправка команды из поля ввода"""
        command = self.command_entry.get().strip()
        if not command:
            return

        self._send_raw_command(command)
        self.command_entry.delete(0, "end")

    def _send_raw_command(self, command):
        """Отправка сырой команды"""
        if not self.is_connected:
            self._add_terminal_line("Нет подключения к устройству", "ERROR")
            return

        try:
            # Добавляем команду в терминал
            self._add_terminal_line(f"→ {command}", "SENT")

            # Отправляем команду
            self.serial_connection.write((command + '\r\n').encode('utf-8'))

            self.logger.log_command_sent("LoRa Link", command)

        except Exception as e:
            self._add_terminal_line(f"Ошибка отправки команды: {e}", "ERROR")
            self.logger.log_error("Command send error", str(e))

    def _clear_terminal(self):
        """Очистка терминала"""
        self.terminal_text.config(state="normal")
        self.terminal_text.delete("1.0", "end")
        self.terminal_text.config(state="disabled")
        self._add_terminal_line("Терминал очищен", "INFO")

    # Команды устройства
    def _ping_device(self):
        """Ping устройства"""
        self._send_raw_command("AT+PING")

    def _get_status(self):
        """Получение статуса устройства"""
        self._send_raw_command("AT+STATUS")

    def _reset_device(self):
        """Сброс устройства"""
        if messagebox.askyesno("Подтверждение", "Перезагрузить LoRa Link?"):
            self._send_raw_command("AT+RESET")

    def _get_version(self):
        """Получение версии прошивки"""
        self._send_raw_command("AT+VERSION")

    def _bind_satellite(self):
        """Привязка спутника"""
        result = messagebox.askstring(
            "Bind Satellite",
            "Введите ID спутника для привязки:",
            initialvalue="SAT001"
        )

        if result:
            self._send_raw_command(f"AT+BIND={result}")
            self._add_terminal_line(f"Запрос привязки спутника: {result}", "INFO")

    def _read_blackbox(self):
        """Считывание блэкбокса"""
        if not self.is_connected:
            messagebox.showerror("Ошибка", "Нет подключения к LoRa Link")
            return

        # Запрашиваем файл для сохранения
        filename = filedialog.asksaveasfilename(
            title="Сохранить блэкбокс",
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("All files", "*.*")],
            initialdir=AppSettings.DATA_DIR
        )

        if filename:
            self._add_terminal_line("Начало считывания блэкбокса...", "INFO")
            self._send_raw_command("AT+BLACKBOX")
            # В реальной реализации здесь будет логика сохранения данных в файл

    def _upload_firmware(self):
        """Загрузка прошивки"""
        filename = filedialog.askopenfilename(
            title="Выберите файл прошивки",
            filetypes=[("Firmware files", "*.hex *.bin"), ("All files", "*.*")]
        )

        if filename:
            result = messagebox.askyesno(
                "Подтверждение",
                f"Загрузить прошивку из файла:\n{filename}\n\n"
                "ВНИМАНИЕ: Процесс может занять несколько минут!"
            )

            if result:
                self._add_terminal_line(f"Начало загрузки прошивки: {filename}", "INFO")
                # В реальной реализации здесь будет логика загрузки прошивки

    def _read_lora_settings(self):
        """Чтение настроек LoRa"""
        self._send_raw_command("AT+CONFIG?")

    def _write_lora_settings(self):
        """Запись настроек LoRa"""
        freq = self.lora_freq_var.get()
        addr = self.lora_addr_var.get()
        key = self.lora_key_var.get()

        commands = [
            f"AT+FREQ={freq}",
            f"AT+ADDR={addr}",
            f"AT+KEY={key}"
        ]

        for cmd in commands:
            self._send_raw_command(cmd)
            time.sleep(0.1)  # Небольшая задержка между командами

    def _save_log(self):
        """Сохранение лога в файл"""
        filename = filedialog.asksaveasfilename(
            title="Сохранить лог терминала",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=AppSettings.DATA_DIR
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    content = self.terminal_text.get("1.0", "end-1c")
                    f.write(content)

                messagebox.showinfo("Успех", f"Лог сохранен в:\n{filename}")
                self.logger.log_file_operation("save terminal log", filename, "success")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить лог:\n{e}")
                self.logger.log_error("Save log error", str(e))

    def _load_commands(self):
        """Загрузка команд из файла"""
        filename = filedialog.askopenfilename(
            title="Загрузить файл команд",
            filetypes=[("Text files", "*.txt"), ("Command files", "*.cmd"), ("All files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    commands = f.readlines()

                self._add_terminal_line(f"Загружен файл команд: {filename}", "INFO")

                for command in commands:
                    command = command.strip()
                    if command and not command.startswith('#'):  # Пропускаем комментарии
                        self._send_raw_command(command)
                        time.sleep(0.2)  # Задержка между командами

                self.logger.log_file_operation("load commands", filename, "success")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить команды:\n{e}")
                self.logger.log_error("Load commands error", str(e))