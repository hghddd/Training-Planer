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
        self.combo_type = ttk.Combobox(self.frame_input, values=["Бег", "Силовая", "Йога", "Плавание", "Другое"])
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
        self.combo_filter_type = ttk.Combobox(self.frame_filter, values=["Все", "Бег", "Силовая", "Йога", "Плавание", "Другое"])
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

        root.columnconfigure(1, weight=1) # Растягиваем колонку с таблицей
        root.rowconfigure(0, weight=1) # Растягиваем строку с таблицей

        self.load_trainings() # Загрузка данных при старте
        self.update_table() # Первичное обновление таблицы

    def is_valid_date(self, date_str):
        """Проверяет корректность формата даты."""
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
        """Добавляет новую тренировку в список и сохраняет данные."""
        date = self.entry_date.get()
        training_type = self.combo_type.get()
        duration = self.entry_duration.get()

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

        self.trainings.append({"date": date, "type": training_type, "duration": int(duration)})
        self.save_trainings()
        self.update_table()
        self.clear_input_fields()

    def clear_input_fields(self):
        """Очищает поля ввода после добавления тренировки."""
        self.entry_date.delete(0, tk.END)
        self.combo_type.set("")
        self.entry_duration.delete(0, tk.END)

    def filter_trainings(self):
        """Фильтрует тренировки по дате и типу."""
        filter_date = self.entry_filter_date.get().lower()
        filter_type = self.combo_filter_type.get().lower()

        filtered_list = []
        for training in self.trainings:
            match_date = not filter_date or filter_date in training["date"].lower()
            match_type = filter_type == "все" or filter_type == training["type"].lower()

            if match_date and match_type:
                filtered_list.append(training)
        self.update_table(filtered_list) # Обновляем таблицу отфильтрованными данными

    def update_table(self, data=None):
        """Обновляет отображение таблицы тренировок."""
        # Очищаем текущие записи
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Опредеtree.insert("", tk.END, values=(training["date"], training["type"], training["duration"]))

    def save_trainings(self):
        """Сохраняет текущий список тренировок в JSON-файл."""
        with open(self.file_path, 'w') as f:
            json.dump(self.trainings, f, indent=4)

        # --- Интеграция с Git ---
        try:
            # Проверяем, инициализирован ли git
            if not os.path.exists(".git"):
                subprocess.run(["git", "init"], check=True, capture_output=True)

            # Добавляем файл trainings.json и другие релевантные файлы
            subprocess.run(["git", "add", self.file_path, "*.py", "README.md", ".gitignore"], check=True, capture_output=True)

            # Делаем коммит, если есть изменения
            status_result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
            if status_result.stdout:], check=True, capture_output=True)
        except FileNotFoundError:
            print("Git не найден. Установите Git для использования этой функции.")
        except subprocess.CalledProcessError as e:
            print(f"Ошибка Git: {e.stderr.decode().strip()}")

    def load_trainings(self):
        """Загружает тренировки из JSON-файла."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    self.trainings = json.load(f)
            except json.JSONDecodeError:
                self.trainings = [] # Если файл пустой или некорректен

if __name__ == "__main__":
    # --- Создание .gitignore, если он не существует ---
    if not os.path.exists(".gitignore"):
        with open(".gitignore", "w") as f:
            f.write("*.pyc\n__pycache__/\n")

    # --- Создание README.md, если он не существует ---
    if not os.path.exists("README.md"):
        readme_content = """
# Training Planner

Приложение для планирования тренировок с сохранением данных в JSON и автоматическим Git-коммитом.

**Основные функции:**
- Добавление новых тренировок.
- Валидация ввода даты и длительности.
- Фильтрация по дате и типу тренировки.
- Сохранение и загрузка данных в `trainings.json`.
- Автоматический коммит изменений в Git при добавлении тренировки.

**Установка и запуск:**
1. Убедитесь, что у вас установлен Python и Git.
2. Скачайте код `training_planner.py`.
3. Запустите приложение: `python training_planner.py`
"""
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)

    root = tk.Tk()
    app = TrainingPlannerApp(root)
    root.mainloop()
    app.save_trainings() # Финальное сохранение при закрытии приложения
