import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime
import os
import subprocess

class TrainingPlannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Training Planner")

        self.trainings = []
        self.file_path = "trainings.json"  # Файл для хранения данных

        # --- Секция ввода данных ---
        self.frame_input = tk.LabelFrame(root, text="Добавить тренировку")
        self.frame_input.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        tk.Label(self.frame_input, text="Дата (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_date = tk.Entry(self.frame_input)
        self.entry_date.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(self.frame_input, text="Тип тренировки:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        # Предопределенный список типов тренировок
        self.training_types = ["Бег", "Силовая", "Йога", "Плавание", "Другое"]
        self.combo_type = ttk.Combobox(self.frame_input, values=self.training_types)
        self.combo_type.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(self.frame_input, text="Длительность (мин):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.entry_duration = tk.Entry(self.frame_input)
        self.entry_duration.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.button_add = tk.Button(self.frame_input, text="Добавить тренировку", command=self.add_training)
        self.button_add.grid(row=3, column=0, columnspan=2, padx=5, pady=10)
        self.frame_input.columnconfigure(1, weight=1)

        # --- Секция фильтрации ---
        self.frame_filter = tk.LabelFrame(root, text="Фильтр")
        self.frame_filter.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        tk.Label(self.frame_filter, text="По дате:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_filter_date = tk.Entry(self.frame_filter)
        self.entry_filter_date.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.entry_filter_date.bind("<KeyRelease>", lambda event=None: self.filter_trainings()) # Фильтр при вводе

        tk.Label(self.frame_filter, text="По типу:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        # Добавляем "Все" для возможности сброса фильтра типа
        filter_types = ["Все"] + self.training_types
        self.combo_filter_type = ttk.Combobox(self.frame_filter, values=filter_types)
        self.combo_filter_type.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.combo_filter_type.set("Все")
        self.combo_filter_type.bind("<<ComboboxSelected>>", lambda event=None: self.filter_trainings()) # Фильтр при выборе
        self.frame_filter.columnconfigure(1, weight=1)

        # --- Таблица для отображения тренировок ---
        self.frame_table = tk.LabelFrame(root, text="Список тренировок")
        self.frame_table.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="nsew")

        self.tree = ttk.Treeview(self.frame_table, columns=("Date", "Type", "Duration"), show="headings")
        self.tree.heading("Date", text="Дата")
        self.tree.heading("Type", text="Тип")
        self.tree.heading("Duration", text="Длительность (мин)")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.frame_table, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Конфигурация растягивания виджетов
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        self.load_trainings() # Загрузка данных при старте
        self.update_table() # Первичное обновление таблицы

    def is_valid_date(self, date_str):
        """Проверяет корректность формата даты (YYYY-MM-DD)."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def is_valid_duration(self, duration_str):
        """Проверяет, является ли длительность положительным числом."""
        try:
            duration = int(duration_str)
            return duration > 0
        except ValueError:
            return False

    def add_training(self):
        """Добавляет новую тренировку, проверяя корректность, и сохраняет данные."""
        date = self.entry_date.get().strip()
        training_type = self.combo_type.get().strip()
        duration = self.entry_duration.get().strip()

        # Валидация ввода
        if not self.is_valid_date(date):
            messagebox.showerror("Ошибка ввода", "Некорректный формат даты. Используйте YYYY-MM-DD.")
            return
        if not training_type:
            messagebox.showerror("Ошибка ввода", "Выберите тип тренировки.")
            return
        if not self.is_valid_duration(duration):
            messagebox.showerror("Ошибка ввода", "Длительность должна быть положительным числом.")
            return

        # Добавление новой тренировки
        self.trainings.append({"date": date, "type": training_type, "duration": int(duration)})
        self.save_trainings() # Сохранить данные после добавления
        self.update_table()   # Обновить таблицу
        self.clear_input_fields() # Очистить поля ввода

    def clear_input_fields(self):
        """Очищает поля ввода."""
        self.entry_date.delete(0, tk.END)
        self.combo_type.set("")
        self.entry_duration.delete(0, tk.END)

    def filter_trainings(self):
        """Фильтрует записи по дате и типу."""
        filter_date = self.entry_filter_date.get().strip().lower()
        filter_type = self.combo_filter_type.get().strip().lower()

        filtered_list = []
        for training in self.trainings:
            # Проверка соответствия дате (частичное совпадение)
            match_date = not filter_date or filter_date in training["date"].lower()
            # Проверка соответствия типу (или "все")
            match_type = filter_type == "все" or filter_type == training["type"].lower()

            if match_date and match_type:
                filtered_list.append(training)

        self.update_table(filtered_list) # Обновляем таблицу с отфильтрованными данными

    def update_table(self, data=None):
        """Обновляет таблицу с данными. Если 'data' предоставлена, используется она."""
        # Очищаем существующие элементы таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Определяем источник данных: либо отфильтрованные, tk.END, values=(training["date"], training["type"], training["duration"]))

    def save_trainings(self):
        """Сохраняет текущий список тренировок в JSON-файл."""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.trainings, f, indent=4, ensure_ascii=False)
            self.git_commit() # Автоматический коммит после сохранения
        except IOError as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить данные: {e}")

    def load_trainings(self):
        """Загружает тренировки из JSON-файла при запуске приложения."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.trainings = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.trainings = [] # Если файл пуст или некорректен, начинаем с пустого списка

    def git_commit(self):
        """Выполняет команды Git для добавления файла и коммита."""
        try:
            # Проверяем, инициализирован ли Git
            if not os.path.exists(".git"):
                subprocess.run(["git", "init"], check=True, capture_output=True, text=True)

            # Добавляем файл данных и скрипт Python (если они изменились)
            subprocess.run(["git", "add", self.file_path, os.path.basename(__file__)], check=True, capture_output=True, text=True)

            # Создаем коммит с сообщением
            commit_message = f"Update trainings data on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(["git", "commit", "-m", commit_message], check=True, capture_output=True, text=True)
            print(f"Git commit successful: '{commit_message}'")
        except FileNotFoundError:
            print("Git не найден. Пожалуйста, установите Git для использования автоматического коммита.")
        except subprocess.CalledProcessError as e:
            # Игнорируем ошибку, если нет изменений для коммита
            if "nothing to commit" not in e.stderr.lower():
                print(f"Ошибка Git: {e.stderr.strip()}")
        except Exception as e:
            print(f"Непредвиденная ошибка Git: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TrainingPlannerApp(root)
    root.mainloop()
    # Финальное сохранение при закрытии приложения
    app.save_trainings()
