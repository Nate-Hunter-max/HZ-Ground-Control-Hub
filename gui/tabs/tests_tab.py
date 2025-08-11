"""
Вкладка тестирования устройства
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
from utils.logger import GCHLogger


class TestsTab(ttk.Frame):
    """Вкладка для проведения тестов устройства"""

    def __init__(self, parent):
        super().__init__(parent)
        self.logger = GCHLogger(__name__)

        # Состояние тестов
        self.test_running = False
        self.test_results = {}

        self._create_widgets()

    def _create_widgets(self):
        """Создание виджетов вкладки"""

        # Главный контейнер с разделением
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Левая панель - управление тестами
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        self._create_test_controls(left_frame)

        # Правая панель - результаты
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        self._create_results_panel(right_frame)

    def _create_test_controls(self, parent):
        """Создание панели управления тестами"""

        # Тест взлета
        takeoff_frame = ttk.LabelFrame(parent, text="Тест взлета", padding=10)
        takeoff_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(
            takeoff_frame,
            text="Симуляция взлета с подменой\nпоказаний датчика давления",
            justify="left"
        ).pack(anchor="w", pady=(0, 10))

        self.takeoff_button = ttk.Button(
            takeoff_frame,
            text="Запустить тест взлета",
            command=self._run_takeoff_test
        )
        self.takeoff_button.pack(fill="x")

        # Статус теста взлета
        self.takeoff_status = ttk.Label(
            takeoff_frame,
            text="Тест не запущен",
            foreground="gray"
        )
        self.takeoff_status.pack(pady=5)

        # Прогресс-бар для теста взлета
        self.takeoff_progress = ttk.Progressbar(
            takeoff_frame,
            mode='determinate'
        )
        self.takeoff_progress.pack(fill="x", pady=5)

        # Предстартовый тест
        prelaunch_frame = ttk.LabelFrame(parent, text="Предстартовый тест", padding=10)
        prelaunch_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(
            prelaunch_frame,
            text="Проверка всех систем и датчиков\nперед запуском",
            justify="left"
        ).pack(anchor="w", pady=(0, 10))

        self.prelaunch_button = ttk.Button(
            prelaunch_frame,
            text="Запустить предстартовый тест",
            command=self._run_prelaunch_test
        )
        self.prelaunch_button.pack(fill="x")

        # Статус предстартового теста
        self.prelaunch_status = ttk.Label(
            prelaunch_frame,
            text="Тест не запущен",
            foreground="gray"
        )
        self.prelaunch_status.pack(pady=5)

        # Прогресс-бар для предстартового теста
        self.prelaunch_progress = ttk.Progressbar(
            prelaunch_frame,
            mode='determinate'
        )
        self.prelaunch_progress.pack(fill="x", pady=5)

        # Комплексный тест
        full_frame = ttk.LabelFrame(parent, text="Комплексный тест", padding=10)
        full_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(
            full_frame,
            text="Полная проверка всех систем\nи функций устройства",
            justify="left"
        ).pack(anchor="w", pady=(0, 10))

        self.full_test_button = ttk.Button(
            full_frame,
            text="Запустить полный тест",
            command=self._run_full_test
        )
        self.full_test_button.pack(fill="x")

        # Статус полного теста
        self.full_status = ttk.Label(
            full_frame,
            text="Тест не запущен",
            foreground="gray"
        )
        self.full_status.pack(pady=5)

        # Прогресс-бар для полного теста
        self.full_progress = ttk.Progressbar(
            full_frame,
            mode='determinate'
        )
        self.full_progress.pack(fill="x", pady=5)

        # Кнопка остановки тестов
        ttk.Button(
            parent,
            text="Остановить все тесты",
            command=self._stop_tests
        ).pack(fill="x", padx=5, pady=10)

    def _create_results_panel(self, parent):
        """Создание панели результатов"""

        # Заголовок
        ttk.Label(
            parent,
            text="Результаты тестирования",
            font=("Arial", 14, "bold")
        ).pack(pady=(0, 10))

        # Таблица результатов
        self._create_results_table(parent)

        # Детальная информация
        self._create_details_panel(parent)

        # Кнопки управления результатами
        self._create_results_controls(parent)

    def _create_results_table(self, parent):
        """Создание таблицы результатов тестов"""
        table_frame = ttk.LabelFrame(parent, text="Сводка тестов", padding=5)
        table_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Создание Treeview для таблицы
        columns = ("test", "status", "result", "time", "details")
        self.results_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=8
        )

        # Настройка заголовков
        headers = {
            "test": "Тест",
            "status": "Статус",
            "result": "Результат",
            "time": "Время",
            "details": "Детали"
        }

        for col, header in headers.items():
            self.results_tree.heading(col, text=header)
            self.results_tree.column(col, width=100)

        # Настройка ширины колонок
        self.results_tree.column("test", width=150)
        self.results_tree.column("status", width=80)
        self.results_tree.column("result", width=80)
        self.results_tree.column("time", width=120)
        self.results_tree.column("details", width=200)

        # Прокрутка для таблицы
        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=tree_scroll.set)

        # Размещение
        self.results_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        # Привязка события выбора
        self.results_tree.bind("<<TreeviewSelect>>", self._on_result_select)

        # Настройка тегов для цветовой индикации
        self.results_tree.tag_configure("success", foreground="green")
        self.results_tree.tag_configure("failure", foreground="red")
        self.results_tree.tag_configure("warning", foreground="orange")
        self.results_tree.tag_configure("running", foreground="blue")

    def _create_details_panel(self, parent):
        """Создание панели детальной информации"""
        details_frame = ttk.LabelFrame(parent, text="Детальная информация", padding=5)
        details_frame.pack(fill="x", padx=5, pady=5)

        # Текстовое поле для подробностей
        text_frame = ttk.Frame(details_frame)
        text_frame.pack(fill="both", expand=True)

        self.details_text = tk.Text(
            text_frame,
            height=6,
            wrap=tk.WORD,
            font=("Courier", 9),
            state="disabled"
        )

        details_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scroll.set)

        self.details_text.pack(side="left", fill="both", expand=True)
        details_scroll.pack(side="right", fill="y")

    def _create_results_controls(self, parent):
        """Создание кнопок управления результатами"""
        controls_frame = ttk.Frame(parent)
        controls_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(
            controls_frame,
            text="Очистить результаты",
            command=self._clear_results
        ).pack(side="left", padx=5)

        ttk.Button(
            controls_frame,
            text="Экспорт в файл",
            command=self._export_results
        ).pack(side="left", padx=5)

        ttk.Button(
            controls_frame,
            text="Обновить",
            command=self._refresh_results
        ).pack(side="left", padx=5)

        # Индикатор общего статуса
        self.overall_status = ttk.Label(
            controls_frame,
            text="Готов к тестированию",
            font=("Arial", 10, "bold"),
            foreground="blue"
        )
        self.overall_status.pack(side="right", padx=10)

    # Методы запуска тестов
    def _run_takeoff_test(self):
        """Запуск теста взлета"""
        if self.test_running:
            messagebox.showwarning("Предупреждение", "Уже выполняется другой тест!")
            return

        self.test_running = True
        self.takeoff_button.config(state="disabled")
        self.takeoff_status.config(text="Выполняется...", foreground="blue")
        self.takeoff_progress['value'] = 0

        # Добавляем запись в таблицу
        test_id = self._add_test_result("Тест взлета", "Выполняется", "-", datetime.now(), "Начало теста")

        # Запускаем тест в отдельном потоке
        thread = threading.Thread(target=self._takeoff_test_worker, args=(test_id,), daemon=True)
        thread.start()

        self.logger.log_test_result("takeoff_test", "started")

    def _takeoff_test_worker(self, test_id):
        """Рабочий поток теста взлета"""
        try:
            stages = [
                ("Инициализация датчиков", 1),
                ("Подмена показаний давления", 2),
                ("Проверка реакции системы", 3),
                ("Анализ алгоритма взлета", 2),
                ("Восстановление датчиков", 1),
                ("Финализация теста", 1)
            ]

            total_time = sum(stage[1] for stage in stages)
            current_progress = 0

            details = []
            success = True

            for stage_name, duration in stages:
                self.after(0, lambda s=stage_name: self.takeoff_status.config(text=f"Выполняется: {s}"))
                details.append(f"[{datetime.now().strftime('%H:%M:%S')}] {stage_name}")

                # Симуляция выполнения этапа
                for i in range(duration * 10):  # 10 итераций в секунду
                    time.sleep(0.1)
                    progress = (current_progress + i / 10) / total_time * 100
                    self.after(0, lambda p=progress: setattr(self.takeoff_progress, 'value', p))

                current_progress += duration

                # Симуляция возможной ошибки
                if stage_name == "Анализ алгоритма взлета" and False:  # Для демонстрации
                    success = False
                    details.append(f"[{datetime.now().strftime('%H:%M:%S')}] ОШИБКА: Неверная реакция на изменение давления")
                    break

            # Завершение теста
            result = "PASS" if success else "FAIL"
            result_details = "\n".join(details)

            self.after(0, lambda: self._finish_takeoff_test(test_id, result, result_details))

        except Exception as e:
            self.logger.log_error("Takeoff test error", str(e))
            self.after(0, lambda: self._finish_takeoff_test(test_id, "ERROR", f"Ошибка выполнения: {e}"))

    def _finish_takeoff_test(self, test_id, result, details):
        """Завершение теста взлета"""
        self.test_running = False
        self.takeoff_button.config(state="normal")

        if result == "PASS":
            self.takeoff_status.config(text="Тест пройден", foreground="green")
            tag = "success"
        elif result == "FAIL":
            self.takeoff_status.config(text="Тест провален", foreground="red")
            tag = "failure"
        else:
            self.takeoff_status.config(text="Ошибка теста", foreground="red")
            tag = "failure"

        self.takeoff_progress['value'] = 100

        # Обновляем запись в таблице
        self._update_test_result(test_id, "Завершен", result, details, tag)

        self.logger.log_test_result("takeoff_test", result, details)

    def _run_prelaunch_test(self):
        """Запуск предстартового теста"""
        if self.test_running:
            messagebox.showwarning("Предупреждение", "Уже выполняется другой тест!")
            return

        self.test_running = True
        self.prelaunch_button.config(state="disabled")
        self.prelaunch_status.config(text="Выполняется...", foreground="blue")
        self.prelaunch_progress['value'] = 0

        # Добавляем запись в таблицу
        test_id = self._add_test_result("Предстартовый тест", "Выполняется", "-", datetime.now(), "Начало теста")

        # Запускаем тест в отдельном потоке
        thread = threading.Thread(target=self._prelaunch_test_worker, args=(test_id,), daemon=True)
        thread.start()

        self.logger.log_test_result("prelaunch_test", "started")

    def _prelaunch_test_worker(self, test_id):
        """Рабочий поток предстартового теста"""
        try:
            sensors = [
                ("Барометр", "OK", "1013.25 hPa"),
                ("Акселерометр", "OK", "X:0.1 Y:0.0 Z:9.8 m/s²"),
                ("Гироскоп", "OK", "X:0.0 Y:0.0 Z:0.0 °/s"),
                ("GPS модуль", "OK", "8 спутников"),
                ("LoRa радио", "OK", "RSSI: -65 dBm"),
                ("Память (SD)", "OK", "15.2 GB свободно"),
                ("Батарея", "WARNING", "6.8V (низкий заряд)"),
                ("Серво приводы", "OK", "Тест движения пройден"),
                ("Парашютная система", "OK", "Датчик раскрытия активен")
            ]

            details = []
            warnings = 0
            errors = 0

            for i, (sensor, status, value) in enumerate(sensors):
                progress = (i + 1) / len(sensors) * 100
                self.after(0, lambda p=progress: setattr(self.prelaunch_progress, 'value', p))
                self.after(0, lambda s=sensor: self.prelaunch_status.config(text=f"Проверка: {s}"))

                # Симуляция времени проверки
                time.sleep(0.5)

                details.append(f"{sensor:20} | {status:8} | {value}")

                if status == "WARNING":
                    warnings += 1
                elif status == "FAIL":
                    errors += 1

            # Определяем общий результат
            if errors > 0:
                result = "FAIL"
            elif warnings > 0:
                result = "WARNING"
            else:
                result = "PASS"

            result_details = "Результаты проверки датчиков:\n" + "\n".join(details)
            result_details += f"\n\nСводка: {len(sensors)} датчиков, {warnings} предупреждений, {errors} ошибок"

            self.after(0, lambda: self._finish_prelaunch_test(test_id, result, result_details))

        except Exception as e:
            self.logger.log_error("Prelaunch test error", str(e))
            self.after(0, lambda: self._finish_prelaunch_test(test_id, "ERROR", f"Ошибка выполнения: {e}"))

    def _finish_prelaunch_test(self, test_id, result, details):
        """Завершение предстартового теста"""
        self.test_running = False
        self.prelaunch_button.config(state="normal")

        if result == "PASS":
            self.prelaunch_status.config(text="Все системы готовы", foreground="green")
            tag = "success"
        elif result == "WARNING":
            self.prelaunch_status.config(text="Есть предупреждения", foreground="orange")
            tag = "warning"
        else:
            self.prelaunch_status.config(text="Обнаружены ошибки", foreground="red")
            tag = "failure"

        self.prelaunch_progress['value'] = 100

        # Обновляем запись в таблице
        self._update_test_result(test_id, "Завершен", result, details, tag)

        self.logger.log_test_result("prelaunch_test", result, details)

    def _run_full_test(self):
        """Запуск полного теста"""
        if self.test_running:
            messagebox.showwarning("Предупреждение", "Уже выполняется другой тест!")
            return

        result = messagebox.askyesno(
            "Подтверждение",
            "Полный тест займет несколько минут и включает все проверки.\n"
            "Продолжить?"
        )

        if not result:
            return

        self.test_running = True
        self.full_test_button.config(state="disabled")
        self.full_status.config(text="Выполняется...", foreground="blue")
        self.full_progress['value'] = 0

        # Добавляем запись в таблицу
        test_id = self._add_test_result("Полный тест", "Выполняется", "-", datetime.now(), "Начало комплексного тестирования")

        # Запускаем тест в отдельном потоке
        thread = threading.Thread(target=self._full_test_worker, args=(test_id,), daemon=True)
        thread.start()

        self.logger.log_test_result("full_test", "started")

    def _full_test_worker(self, test_id):
        """Рабочий поток полного теста"""
        try:
            test_stages = [
                ("Предстартовая проверка", 15),
                ("Тест взлетной логики", 20),
                ("Проверка телеметрии", 10),
                ("Тест системы спасения", 25),
                ("Проверка радиосвязи", 15),
                ("Функциональные тесты", 20),
                ("Стресс-тест памяти", 10),
                ("Финальная верификация", 5)
            ]

            total_duration = sum(stage[1] for stage in test_stages)
            current_time = 0
            details = []
            overall_success = True

            for stage_name, duration in test_stages:
                self.after(0, lambda s=stage_name: self.full_status.config(text=f"Выполняется: {s}"))
                details.append(f"\n=== {stage_name} ===")
                details.append(f"Начало: {datetime.now().strftime('%H:%M:%S')}")

                # Симуляция выполнения этапа
                for i in range(duration):
                    time.sleep(0.2)  # Ускоренная симуляция
                    progress = (current_time + i) / total_duration * 100
                    self.after(0, lambda p=progress: setattr(self.full_progress, 'value', p))

                # Симуляция результатов этапа
                stage_success = True  # В реальности здесь будет логика проверки

                if stage_success:
                    details.append("Результат: PASS")
                else:
                    details.append("Результат: FAIL")
                    overall_success = False

                details.append(f"Завершение: {datetime.now().strftime('%H:%M:%S')}")
                current_time += duration

            # Формируем финальный отчет
            result = "PASS" if overall_success else "FAIL"
            result_details = "\n".join(details)
            result_details += f"\n\n=== СВОДКА ===\nОбщий результат: {result}\nВремя выполнения: {total_duration * 0.2:.1f} сек"

            self.after(0, lambda: self._finish_full_test(test_id, result, result_details))

        except Exception as e:
            self.logger.log_error("Full test error", str(e))
            self.after(0, lambda: self._finish_full_test(test_id, "ERROR", f"Ошибка выполнения: {e}"))

    def _finish_full_test(self, test_id, result, details):
        """Завершение полного теста"""
        self.test_running = False
        self.full_test_button.config(state="normal")

        if result == "PASS":
            self.full_status.config(text="Все тесты пройдены", foreground="green")
            tag = "success"
        else:
            self.full_status.config(text="Обнаружены проблемы", foreground="red")
            tag = "failure"

        self.full_progress['value'] = 100

        # Обновляем запись в таблице
        self._update_test_result(test_id, "Завершен", result, details, tag)

        self.logger.log_test_result("full_test", result, details)

    def _stop_tests(self):
        """Остановка всех тестов"""
        if not self.test_running:
            messagebox.showinfo("Информация", "Нет выполняющихся тестов")
            return

        result = messagebox.askyesno(
            "Подтверждение",
            "Вы уверены, что хотите остановить выполняющиеся тесты?"
        )

        if result:
            self.test_running = False
            self.takeoff_button.config(state="normal")
            self.prelaunch_button.config(state="normal")
            self.full_test_button.config(state="normal")

            self.takeoff_status.config(text="Тест остановлен", foreground="red")
            self.prelaunch_status.config(text="Тест остановлен", foreground="red")
            self.full_status.config(text="Тест остановлен", foreground="red")

            self.logger.logger.warning("Тесты принудительно остановлены пользователем")

    # Методы управления результатами
    def _add_test_result(self, test_name, status, result, timestamp, details):
        """Добавление результата теста в таблицу"""
        time_str = timestamp.strftime("%H:%M:%S")
        test_id = self.results_tree.insert(
            "",
            "end",
            values=(test_name, status, result, time_str, details[:50] + "..." if len(details) > 50 else details),
            tags=("running",)
        )

        # Сохраняем полные детали
        self.test_results[test_id] = {
            "name": test_name,
            "status": status,
            "result": result,
            "timestamp": timestamp,
            "details": details
        }

        return test_id

    def _update_test_result(self, test_id, status, result, details, tag):
        """Обновление результата теста"""
        if test_id in self.test_results:
            self.test_results[test_id].update({
                "status": status,
                "result": result,
                "details": details
            })

            # Обновляем запись в дереве
            current_values = self.results_tree.item(test_id, "values")
            new_values = (
                current_values[0],  # имя теста
                status,
                result,
                current_values[3],  # время
                details[:50] + "..." if len(details) > 50 else details
            )

            self.results_tree.item(test_id, values=new_values, tags=(tag,))

    def _on_result_select(self, event):
        """Обработчик выбора результата в таблице"""
        selection = self.results_tree.selection()
        if not selection:
            return

        test_id = selection[0]
        if test_id in self.test_results:
            test_data = self.test_results[test_id]

            # Отображаем детальную информацию
            self.details_text.config(state="normal")
            self.details_text.delete("1.0", "end")
            self.details_text.insert("1.0", test_data["details"])
            self.details_text.config(state="disabled")

    def _clear_results(self):
        """Очистка всех результатов"""
        result = messagebox.askyesno(
            "Подтверждение",
            "Очистить все результаты тестов?"
        )

        if result:
            for item in self.results_tree.get_children():
                self.results_tree.delete(item)

            self.test_results.clear()

            self.details_text.config(state="normal")
            self.details_text.delete("1.0", "end")
            self.details_text.config(state="disabled")

            self.logger.logger.info("Результаты тестов очищены")

    def _export_results(self):
        """Экспорт результатов в файл"""
        if not self.test_results:
            messagebox.showinfo("Информация", "Нет результатов для экспорта")
            return

        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            title="Экспорт результатов тестов",
            defaultextension=".txt",
            filetypes=[("Текст", "*.txt"), ("CSV", "*.csv"), ("Все файлы", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=== ОТЧЕТ О ТЕСТИРОВАНИИ HZ GCH ===\n")
                    f.write(f"Дата создания: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                    for test_data in self.test_results.values():
                        f.write(f"Тест: {test_data['name']}\n")
                        f.write(f"Статус: {test_data['status']}\n")
                        f.write(f"Результат: {test_data['result']}\n")
                        f.write(f"Время: {test_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"Детали:\n{test_data['details']}\n")
                        f.write("-" * 50 + "\n\n")

                messagebox.showinfo("Успех", f"Результаты экспортированы в:\n{filename}")
                self.logger.log_file_operation("export test results", filename, "success")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать результаты:\n{e}")
                self.logger.log_error("Export results error", str(e))

    def _refresh_results(self):
        """Обновление отображения результатов"""
        self.logger.logger.info("Обновление результатов тестов")
        # В реальной реализации здесь может быть загрузка результатов из файла или базы данных