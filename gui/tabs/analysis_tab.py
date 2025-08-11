"""
Вкладка анализа данных и графиков
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import pandas as pd
import json
import os
from datetime import datetime
from utils.logger import GCHLogger
from config.settings import AppSettings


class AnalysisTab(ttk.Frame):
    """Вкладка для анализа данных и построения графиков"""

    def __init__(self, parent):
        super().__init__(parent)
        self.logger = GCHLogger(__name__)

        # Данные для анализа
        self.current_data = None
        self.available_columns = []
        self.graphs = {}  # Словарь графиков
        self.current_graph_id = 0

        # Настройки matplotlib
        plt.style.use('default')

        self._create_widgets()
        self._load_plot_config()

    def _create_widgets(self):
        """Создание виджетов вкладки"""

        # Панель управления данными
        self._create_data_control_panel()

        # Основная область с графиками и управлением
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Левая панель - управление графиками
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        self._create_graph_controls(left_frame)

        # Правая панель - область графиков
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=3)
        self._create_plot_area(right_frame)

    def _create_data_control_panel(self):
        """Создание панели управления данными"""
        data_frame = ttk.LabelFrame(self, text="Источник данных", padding=5)
        data_frame.pack(fill="x", padx=5, pady=5)

        # Выбор источника данных
        source_frame = ttk.Frame(data_frame)
        source_frame.pack(fill="x", pady=2)

        ttk.Label(source_frame, text="Источник:").pack(side="left")

        self.data_source_var = tk.StringVar(value="Файл")
        source_combo = ttk.Combobox(
            source_frame,
            textvariable=self.data_source_var,
            values=["Файл", "USB подключение", "LoRa Link"],
            width=15,
            state="readonly"
        )
        source_combo.pack(side="left", padx=5)
        source_combo.bind("<<ComboboxSelected>>", self._on_source_changed)

        # Кнопки управления данными
        buttons_frame = ttk.Frame(data_frame)
        buttons_frame.pack(fill="x", pady=2)

        ttk.Button(
            buttons_frame,
            text="Загрузить файл",
            command=self._load_data_file
        ).pack(side="left", padx=2)

        ttk.Button(
            buttons_frame,
            text="Подключиться к устройству",
            command=self._connect_to_device
        ).pack(side="left", padx=2)

        ttk.Button(
            buttons_frame,
            text="Обновить данные",
            command=self._refresh_data
        ).pack(side="left", padx=2)

        # Информация о данных
        info_frame = ttk.Frame(data_frame)
        info_frame.pack(fill="x", pady=2)

        self.data_info_var = tk.StringVar(value="Данные не загружены")
        ttk.Label(
            info_frame,
            textvariable=self.data_info_var,
            foreground="blue"
        ).pack(side="left")

    def _create_graph_controls(self, parent):
        """Создание панели управления графиками"""

        # CRUD для графиков
        crud_frame = ttk.LabelFrame(parent, text="Управление графиками", padding=5)
        crud_frame.pack(fill="x", pady=5)

        ttk.Button(
            crud_frame,
            text="Добавить график",
            command=self._add_new_graph
        ).pack(fill="x", pady=2)

        ttk.Button(
            crud_frame,
            text="Удалить выбранный",
            command=self._remove_selected_graph
        ).pack(fill="x", pady=2)

        ttk.Button(
            crud_frame,
            text="Очистить все",
            command=self._clear_all_graphs
        ).pack(fill="x", pady=2)

        # Список графиков
        graphs_frame = ttk.LabelFrame(parent, text="Список графиков", padding=5)
        graphs_frame.pack(fill="both", expand=True, pady=5)

        # Создание Treeview для списка графиков
        self.graphs_tree = ttk.Treeview(
            graphs_frame,
            columns=("type", "x_axis", "y_axis"),
            show="tree headings",
            height=8
        )

        # Настройка заголовков
        self.graphs_tree.heading("#0", text="График")
        self.graphs_tree.heading("type", text="Тип")
        self.graphs_tree.heading("x_axis", text="Ось X")
        self.graphs_tree.heading("y_axis", text="Ось Y")

        # Ширина колонок
        self.graphs_tree.column("#0", width=100)
        self.graphs_tree.column("type", width=80)
        self.graphs_tree.column("x_axis", width=80)
        self.graphs_tree.column("y_axis", width=80)

        # Прокрутка
        graphs_scroll = ttk.Scrollbar(graphs_frame, orient="vertical", command=self.graphs_tree.yview)
        self.graphs_tree.configure(yscrollcommand=graphs_scroll.set)

        self.graphs_tree.pack(side="left", fill="both", expand=True)
        graphs_scroll.pack(side="right", fill="y")

        # Привязка событий
        self.graphs_tree.bind("<<TreeviewSelect>>", self._on_graph_select)
        self.graphs_tree.bind("<Double-1>", self._edit_graph)

        # Панель настроек выбранного графика
        self._create_graph_settings_panel(parent)

        # Управление конфигурациями
        self._create_config_panel(parent)

    def _create_graph_settings_panel(self, parent):
        """Создание панели настроек графика"""
        settings_frame = ttk.LabelFrame(parent, text="Настройки графика", padding=5)
        settings_frame.pack(fill="x", pady=5)

        # Тип графика
        type_frame = ttk.Frame(settings_frame)
        type_frame.pack(fill="x", pady=2)

        ttk.Label(type_frame, text="Тип:", width=8).pack(side="left")
        self.graph_type_var = tk.StringVar(value="line")
        type_combo = ttk.Combobox(
            type_frame,
            textvariable=self.graph_type_var,
            values=["line", "scatter", "bar", "histogram"],
            width=12,
            state="readonly"
        )
        type_combo.pack(side="left", padx=2)

        # Ось X
        x_frame = ttk.Frame(settings_frame)
        x_frame.pack(fill="x", pady=2)

        ttk.Label(x_frame, text="Ось X:", width=8).pack(side="left")
        self.x_axis_var = tk.StringVar()
        self.x_combo = ttk.Combobox(
            x_frame,
            textvariable=self.x_axis_var,
            width=12,
            state="readonly"
        )
        self.x_combo.pack(side="left", padx=2)

        # Ось Y1
        y1_frame = ttk.Frame(settings_frame)
        y1_frame.pack(fill="x", pady=2)

        ttk.Label(y1_frame, text="Ось Y1:", width=8).pack(side="left")
        self.y1_axis_var = tk.StringVar()
        self.y1_combo = ttk.Combobox(
            y1_frame,
            textvariable=self.y1_axis_var,
            width=12,
            state="readonly"
        )
        self.y1_combo.pack(side="left", padx=2)

        # Ось Y2 (опционально)
        y2_frame = ttk.Frame(settings_frame)
        y2_frame.pack(fill="x", pady=2)

        ttk.Label(y2_frame, text="Ось Y2:", width=8).pack(side="left")
        self.y2_axis_var = tk.StringVar()
        self.y2_combo = ttk.Combobox(
            y2_frame,
            textvariable=self.y2_axis_var,
            values=[""] + self.available_columns,
            width=12,
            state="readonly"
        )
        self.y2_combo.pack(side="left", padx=2)

        # Цвет и стиль
        style_frame = ttk.Frame(settings_frame)
        style_frame.pack(fill="x", pady=2)

        ttk.Label(style_frame, text="Цвет:", width=8).pack(side="left")
        self.color_var = tk.StringVar(value="blue")
        color_combo = ttk.Combobox(
            style_frame,
            textvariable=self.color_var,
            values=["blue", "red", "green", "orange", "purple", "brown", "pink", "gray"],
            width=8,
            state="readonly"
        )
        color_combo.pack(side="left", padx=2)

        # Кнопки применения настроек
        apply_frame = ttk.Frame(settings_frame)
        apply_frame.pack(fill="x", pady=5)

        ttk.Button(
            apply_frame,
            text="Применить",
            command=self._apply_graph_settings
        ).pack(side="left", padx=2)

        ttk.Button(
            apply_frame,
            text="Сбросить",
            command=self._reset_graph_settings
        ).pack(side="left", padx=2)

    def _create_config_panel(self, parent):
        """Создание панели управления конфигурациями"""
        config_frame = ttk.LabelFrame(parent, text="Конфигурации графиков", padding=5)
        config_frame.pack(fill="x", pady=5)

        ttk.Button(
            config_frame,
            text="Сохранить конфигурацию",
            command=self._save_plot_config
        ).pack(fill="x", pady=1)

        ttk.Button(
            config_frame,
            text="Загрузить конфигурацию",
            command=self._load_plot_config_file
        ).pack(fill="x", pady=1)

        # Экспорт
        export_frame = ttk.LabelFrame(config_frame, text="Экспорт", padding=3)
        export_frame.pack(fill="x", pady=3)

        ttk.Button(
            export_frame,
            text="Экспорт PNG",
            command=lambda: self._export_plot("png")
        ).pack(side="left", padx=1)

        ttk.Button(
            export_frame,
            text="Экспорт SVG",
            command=lambda: self._export_plot("svg")
        ).pack(side="left", padx=1)

        ttk.Button(
            export_frame,
            text="Экспорт CSV",
            command=self._export_csv
        ).pack(side="left", padx=1)

    def _create_plot_area(self, parent):
        """Создание области для графиков"""
        plot_frame = ttk.LabelFrame(parent, text="Графики", padding=5)
        plot_frame.pack(fill="both", expand=True)

        # Создаем matplotlib фигуру
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.fig.tight_layout(pad=3.0)

        # Интегрируем matplotlib в tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Панель инструментов matplotlib
        toolbar_frame = ttk.Frame(plot_frame)
        toolbar_frame.pack(fill="x", side="bottom")

        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()

        # Начальное сообщение
        self.ax.text(0.5, 0.5, 'Загрузите данные и добавьте график',
                     ha='center', va='center', transform=self.ax.transAxes,
                     fontsize=14, color='gray')
        self.ax.set_title('HZ GCH - Анализ данных полета')
        self.canvas.draw()

    def _load_data_file(self):
        """Загрузка файла с данными"""
        filetypes = [
            ("CSV files", "*.csv"),
            ("Log files", "*.log"),
            ("Binary files", "*.bin"),
            ("All files", "*.*")
        ]

        filename = filedialog.askopenfilename(
            title="Загрузить файл данных",
            filetypes=filetypes,
            initialdir=AppSettings.DATA_DIR
        )

        if filename:
            try:
                # Определяем тип файла и загружаем соответствующим образом
                file_ext = os.path.splitext(filename)[1].lower()

                if file_ext == '.csv':
                    self.current_data = pd.read_csv(filename)
                elif file_ext in ['.log', '.txt']:
                    # Пытаемся загрузить как CSV с табуляцией
                    self.current_data = pd.read_csv(filename, sep='\t', engine='python')
                else:
                    # Для бинарных файлов нужна специальная обработка
                    messagebox.showwarning("Предупреждение",
                                           "Бинарные файлы требуют специального парсера.\n"
                                           "Пока поддерживаются только CSV и текстовые файлы.")
                    return

                # Обновляем доступные колонки
                self.available_columns = list(self.current_data.columns)
                self._update_column_combos()

                # Обновляем информацию о данных
                rows, cols = self.current_data.shape
                self.data_info_var.set(f"Загружен файл: {os.path.basename(filename)} "
                                       f"({rows} записей, {cols} колонок)")

                self.logger.log_file_operation("load data", filename, "success")
                self._refresh_plots()

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить файл:\n{e}")
                self.logger.log_error("Data load error", str(e))

    def _connect_to_device(self):
        """Подключение к устройству для получения данных в реальном времени"""
        source = self.data_source_var.get()
        if source == "USB подключение":
            # TODO: Реализовать подключение по USB
            messagebox.showinfo("Информация", "USB подключение в разработке")
        elif source == "LoRa Link":
            # TODO: Реализовать подключение по LoRa
            messagebox.showinfo("Информация", "LoRa подключение в разработке")

    def _refresh_data(self):
        """Обновление данных"""
        if self.current_data is not None:
            self._refresh_plots()
            self.logger.logger.info("Данные обновлены")
        else:
            messagebox.showinfo("Информация", "Нет загруженных данных")

    def _on_source_changed(self, event=None):
        """Обработчик смены источника данных"""
        source = self.data_source_var.get()
        self.logger.logger.info(f"Выбран источник данных: {source}")

    def _update_column_combos(self):
        """Обновление списков колонок в комбобоксах"""
        values = self.available_columns

        self.x_combo['values'] = values
        self.y1_combo['values'] = values
        self.y2_combo['values'] = [""] + values

        # Устанавливаем значения по умолчанию
        if values:
            if 'timestamp' in values or 'time' in values:
                default_x = 'timestamp' if 'timestamp' in values else 'time'
                self.x_axis_var.set(default_x)
            else:
                self.x_axis_var.set(values[0])

            if len(values) > 1:
                self.y1_axis_var.set(values[1])

    def _add_new_graph(self):
        """Добавление нового графика"""
        if not self.available_columns:
            messagebox.showwarning("Предупреждение", "Сначала загрузите данные")
            return

        self.current_graph_id += 1
        graph_name = f"График {self.current_graph_id}"

        # Добавляем в список
        graph_id = self.graphs_tree.insert(
            "",
            "end",
            text=graph_name,
            values=("line", self.x_axis_var.get(), self.y1_axis_var.get())
        )

        # Сохраняем настройки графика
        self.graphs[graph_id] = {
            "name": graph_name,
            "type": "line",
            "x_axis": self.x_axis_var.get(),
            "y1_axis": self.y1_axis_var.get(),
            "y2_axis": "",
            "color": "blue",
            "visible": True
        }

        self._refresh_plots()
        self.logger.logger.info(f"Добавлен график: {graph_name}")

    def _remove_selected_graph(self):
        """Удаление выбранного графика"""
        selection = self.graphs_tree.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите график для удаления")
            return

        for graph_id in selection:
            graph_name = self.graphs[graph_id]["name"]
            self.graphs_tree.delete(graph_id)
            del self.graphs[graph_id]
            self.logger.logger.info(f"Удален график: {graph_name}")

        self._refresh_plots()

    def _clear_all_graphs(self):
        """Очистка всех графиков"""
        if not self.graphs:
            return

        result = messagebox.askyesno("Подтверждение", "Удалить все графики?")
        if result:
            for item in self.graphs_tree.get_children():
                self.graphs_tree.delete(item)

            self.graphs.clear()
            self._refresh_plots()
            self.logger.logger.info("Все графики удалены")

    def _on_graph_select(self, event):
        """Обработчик выбора графика в списке"""
        selection = self.graphs_tree.selection()
        if selection:
            graph_id = selection[0]
            if graph_id in self.graphs:
                graph_config = self.graphs[graph_id]

                # Загружаем настройки в форму
                self.graph_type_var.set(graph_config.get("type", "line"))
                self.x_axis_var.set(graph_config.get("x_axis", ""))
                self.y1_axis_var.set(graph_config.get("y1_axis", ""))
                self.y2_axis_var.set(graph_config.get("y2_axis", ""))
                self.color_var.set(graph_config.get("color", "blue"))

    def _edit_graph(self, event):
        """Редактирование графика по двойному клику"""
        selection = self.graphs_tree.selection()
        if selection:
            # В более продвинутой версии здесь может быть диалог редактирования
            self.logger.logger.info("Редактирование графика")

    def _apply_graph_settings(self):
        """Применение настроек к выбранному графику"""
        selection = self.graphs_tree.selection()
        if not selection:
            messagebox.showinfo("Информация", "Выберите график для изменения")
            return

        graph_id = selection[0]
        if graph_id in self.graphs:
            # Обновляем настройки
            self.graphs[graph_id].update({
                "type": self.graph_type_var.get(),
                "x_axis": self.x_axis_var.get(),
                "y1_axis": self.y1_axis_var.get(),
                "y2_axis": self.y2_axis_var.get(),
                "color": self.color_var.get()
            })

            # Обновляем отображение в списке
            self.graphs_tree.item(
                graph_id,
                values=(
                    self.graph_type_var.get(),
                    self.x_axis_var.get(),
                    self.y1_axis_var.get()
                )
            )

            self._refresh_plots()
            self.logger.logger.info("Настройки графика применены")

    def _reset_graph_settings(self):
        """Сброс настроек графика"""
        self.graph_type_var.set("line")
        self.x_axis_var.set("")
        self.y1_axis_var.set("")
        self.y2_axis_var.set("")
        self.color_var.set("blue")

    def _refresh_plots(self):
        """Обновление отображения всех графиков"""
        if self.current_data is None or not self.graphs:
            self.ax.clear()
            self.ax.text(0.5, 0.5, 'Нет данных или графиков для отображения',
                         ha='center', va='center', transform=self.ax.transAxes,
                         fontsize=14, color='gray')
            self.ax.set_title('HZ GCH - Анализ данных полета')
            self.canvas.draw()
            return

        try:
            self.ax.clear()

            # Строим каждый график
            for graph_id, config in self.graphs.items():
                if not config.get("visible", True):
                    continue

                x_col = config.get("x_axis")
                y1_col = config.get("y1_axis")
                y2_col = config.get("y2_axis")
                graph_type = config.get("type", "line")
                color = config.get("color", "blue")

                if not x_col or not y1_col:
                    continue

                if x_col not in self.current_data.columns or y1_col not in self.current_data.columns:
                    continue

                x_data = self.current_data[x_col]
                y1_data = self.current_data[y1_col]

                # Строим основной график
                if graph_type == "line":
                    self.ax.plot(x_data, y1_data, color=color, label=f"{config['name']} ({y1_col})")
                elif graph_type == "scatter":
                    self.ax.scatter(x_data, y1_data, color=color, label=f"{config['name']} ({y1_col})", alpha=0.6)
                elif graph_type == "bar":
                    self.ax.bar(x_data, y1_data, color=color, label=f"{config['name']} ({y1_col})", alpha=0.7)

                # Дополнительная ось Y2 если указана
                if y2_col and y2_col in self.current_data.columns:
                    ax2 = self.ax.twinx()
                    y2_data = self.current_data[y2_col]
                    ax2.plot(x_data, y2_data, color='red', linestyle='--', label=f"{config['name']} ({y2_col})")
                    ax2.set_ylabel(y2_col)
                    ax2.legend(loc='upper right')

            # Настройка осей и легенды
            self.ax.set_xlabel(x_col if x_col else "X")
            self.ax.set_ylabel("Y")
            self.ax.legend(loc='upper left')
            self.ax.grid(True, alpha=0.3)
            self.ax.set_title('Анализ данных полета - HZ GCH')

            # Улучшение внешнего вида
            self.fig.tight_layout()
            self.canvas.draw()

        except Exception as e:
            self.logger.log_error("Plot refresh error", str(e))
            messagebox.showerror("Ошибка", f"Ошибка при построении графиков:\n{e}")

    def _save_plot_config(self):
        """Сохранение конфигурации графиков"""
        if not self.graphs:
            messagebox.showinfo("Информация", "Нет графиков для сохранения")
            return

        filename = filedialog.asksaveasfilename(
            title="Сохранить конфигурацию графиков",
            defaultextension=".gchplot",
            filetypes=[("GCH Plot Config", "*.gchplot"), ("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=AppSettings.CONFIG_DIR
        )

        if filename:
            try:
                config = {
                    "version": "1.0",
                    "created": datetime.now().isoformat(),
                    "data_columns": self.available_columns,
                    "graphs": {}
                }

                # Сохраняем настройки всех графиков
                for graph_id, graph_config in self.graphs.items():
                    config["graphs"][str(graph_id)] = graph_config

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

                messagebox.showinfo("Успех", f"Конфигурация сохранена в:\n{filename}")
                self.logger.log_file_operation("save plot config", filename, "success")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить конфигурацию:\n{e}")
                self.logger.log_error("Save plot config error", str(e))

    def _load_plot_config_file(self):
        """Загрузка конфигурации графиков из файла"""
        filename = filedialog.askopenfilename(
            title="Загрузить конфигурацию графиков",
            filetypes=[("GCH Plot Config", "*.gchplot"), ("JSON files", "*.json"), ("All files", "*.*")],
            initialdir=AppSettings.CONFIG_DIR
        )

        if filename:
            self._load_plot_config(filename)

    def _load_plot_config(self, filename=None):
        """Загрузка конфигурации графиков"""
        if filename is None:
            filename = AppSettings.PLOT_CONFIG_FILE

        if not os.path.exists(filename):
            return

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Очищаем текущие графики
            self._clear_all_graphs()

            # Загружаем графики из конфигурации
            graphs_config = config.get("graphs", {})
            for graph_id_str, graph_config in graphs_config.items():
                graph_id = self.graphs_tree.insert(
                    "",
                    "end",
                    text=graph_config.get("name", f"График {graph_id_str}"),
                    values=(
                        graph_config.get("type", "line"),
                        graph_config.get("x_axis", ""),
                        graph_config.get("y1_axis", "")
                    )
                )

                self.graphs[graph_id] = graph_config

            self._refresh_plots()

            if filename != AppSettings.PLOT_CONFIG_FILE:
                messagebox.showinfo("Успех", "Конфигурация графиков загружена")

            self.logger.log_file_operation("load plot config", filename, "success")

        except Exception as e:
            if filename != AppSettings.PLOT_CONFIG_FILE:
                messagebox.showerror("Ошибка", f"Не удалось загрузить конфигурацию:\n{e}")
            self.logger.log_error("Load plot config error", str(e))

    def _export_plot(self, format_type):
        """Экспорт графика в изображение"""
        if not self.graphs:
            messagebox.showinfo("Информация", "Нет графиков для экспорта")
            return

        filename = filedialog.asksaveasfilename(
            title=f"Экспорт графика в {format_type.upper()}",
            defaultextension=f".{format_type}",
            filetypes=[(f"{format_type.upper()} files", f"*.{format_type}"), ("All files", "*.*")],
            initialdir=AppSettings.DATA_DIR
        )

        if filename:
            try:
                # Сохраняем с высоким разрешением
                self.fig.savefig(filename, format=format_type, dpi=300, bbox_inches='tight')

                messagebox.showinfo("Успех", f"График экспортирован в:\n{filename}")
                self.logger.log_file_operation(f"export plot {format_type}", filename, "success")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать график:\n{e}")
                self.logger.log_error("Export plot error", str(e))

    def _export_csv(self):
        """Экспорт выбранных данных в CSV"""
        if self.current_data is None:
            messagebox.showinfo("Информация", "Нет данных для экспорта")
            return

        # Определяем какие колонки экспортировать
        columns_to_export = set()
        for graph_config in self.graphs.values():
            if graph_config.get("x_axis"):
                columns_to_export.add(graph_config["x_axis"])
            if graph_config.get("y1_axis"):
                columns_to_export.add(graph_config["y1_axis"])
            if graph_config.get("y2_axis"):
                columns_to_export.add(graph_config["y2_axis"])

        if not columns_to_export:
            columns_to_export = self.current_data.columns

        filename = filedialog.asksaveasfilename(
            title="Экспорт данных в CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=AppSettings.DATA_DIR
        )

        if filename:
            try:
                # Экспортируем выбранные колонки
                export_data = self.current_data[list(columns_to_export)]
                export_data.to_csv(filename, index=False)

                messagebox.showinfo("Успех",
                                    f"Данные экспортированы в:\n{filename}\n"
                                    f"Колонки: {len(columns_to_export)}\n"
                                    f"Записи: {len(export_data)}")

                self.logger.log_file_operation("export csv", filename, "success")

            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать данные:\n{e}")
                self.logger.log_error("Export CSV error", str(e))