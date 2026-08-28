# -*- coding: utf-8 -*-
"""
Учёт инвентарных объектов по штрих-кодам EAN13.

Запуск:  python app.py

Что умеет:
  1. Вкладка "Новая наклейка" — генерирует уникальный штрих-код EAN13,
     сохраняет запись (инв. номер, наименование, описание, дата оклейки)
     в inventory.csv и создаёт готовое изображение наклейки 58x40мм
     для термопринтера Xprinter XP-365B (папка labels/).
  2. Вкладка "Действия" — по введённому штрих-коду находит объект в базе,
     позволяет собрать список из нескольких объектов и сформировать
     документ (Word .docx) на списание / передачу / установку
     (папка documents/). После формирования документа статус объектов
     в базе обновляется автоматически.
  3. Вкладка "Проверка базы" — ищет дубликаты штрих-кодов и инвентарных
     номеров, пустые обязательные поля и штрих-коды с неверной
     контрольной суммой EAN13.
"""

import os
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import subprocess
from PIL import ImageTk

import storage
import barcode_utils
import documents

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "inventory.csv")
LABELS_DIR = os.path.join(BASE_DIR, "labels")
DOCS_DIR = os.path.join(BASE_DIR, "documents")

ACTIONS = ["Списание", "Передача", "Установка"]
STATUS_BY_ACTION = {"Списание": "Списан", "Передача": "Передан", "Установка": "Установлен"}

def open_file(path: str) -> None:
    """Открывает файл в программе по умолчанию (Windows/macOS/Linux)."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
    except Exception as exc:
        messagebox.showwarning(
            "Не удалось открыть файл",
            f"Документ сохранён, но открыть автоматически не получилось:\n{exc}\n\nПуть:\n{path}"
        )

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Учёт инвентарных объектов по штрих-кодам")
        self.geometry("760x600")

        os.makedirs(LABELS_DIR, exist_ok=True)
        os.makedirs(DOCS_DIR, exist_ok=True)
        storage.ensure_db(DB_PATH)

        self.queue = []  # список записей, отобранных для текущего документа
        self._preview_photo = None  # хранит ссылку на PhotoImage, чтобы её не удалил GC

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_new = ttk.Frame(notebook)
        self.tab_actions = ttk.Frame(notebook)
        self.tab_verify = ttk.Frame(notebook)

        notebook.add(self.tab_new, text="Новая наклейка")
        notebook.add(self.tab_actions, text="Действия")
        notebook.add(self.tab_verify, text="Проверка базы")

        self._build_tab_new()
        self._build_tab_actions()
        self._build_tab_verify()

    # ------------------------------------------------------------------
    # Вкладка 1: генерация новой наклейки
    # ------------------------------------------------------------------
    def _build_tab_new(self):
        frame = self.tab_new
        pad = {"padx": 6, "pady": 4}

        left = ttk.Frame(frame)
        left.pack(side="left", fill="y", padx=10, pady=10)

        ttk.Label(left, text="Инвентарный номер *").grid(row=0, column=0, sticky="w", **pad)
        self.entry_inv = ttk.Entry(left, width=32)
        self.entry_inv.grid(row=0, column=1, **pad)

        ttk.Label(left, text="Наименование *").grid(row=1, column=0, sticky="w", **pad)
        self.entry_name = ttk.Entry(left, width=32)
        self.entry_name.grid(row=1, column=1, **pad)

        ttk.Label(left, text="Описание").grid(row=2, column=0, sticky="nw", **pad)
        self.text_desc = tk.Text(left, width=32, height=4)
        self.text_desc.grid(row=2, column=1, **pad)

        ttk.Label(left, text="Дата оклейки").grid(row=3, column=0, sticky="w", **pad)
        today = datetime.date.today().strftime("%d.%m.%Y")
        ttk.Label(left, text=today).grid(row=3, column=1, sticky="w", **pad)

        btn = ttk.Button(left, text="Сгенерировать и сохранить наклейку",
                          command=self._generate_label)
        btn.grid(row=4, column=0, columnspan=2, pady=12)

        self.label_result = ttk.Label(left, text="", wraplength=280, justify="left")
        self.label_result.grid(row=5, column=0, columnspan=2, sticky="w", **pad)

        right = ttk.Frame(frame)
        right.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        ttk.Label(right, text="Предпросмотр наклейки:").pack(anchor="w")
        self.preview_canvas = tk.Label(right, relief="groove", background="white")
        self.preview_canvas.pack(fill="both", expand=True, pady=6)

    def _generate_label(self):
        inv = self.entry_inv.get().strip()
        name = self.entry_name.get().strip()
        desc = self.text_desc.get("1.0", "end").strip()

        if not inv or not name:
            messagebox.showerror("Ошибка", "Заполните инвентарный номер и наименование.")
            return

        date_str = datetime.date.today().strftime("%d.%m.%Y")

        try:
            ean = barcode_utils.generate_ean13(BASE_DIR)
            image = barcode_utils.create_label_image(ean, inv, name, desc, date_str)
        except Exception as exc:
            messagebox.showerror("Ошибка генерации", str(exc))
            return

        filename = f"{ean}.png"
        path = os.path.join(LABELS_DIR, filename)
        barcode_utils.save_label_image(image, path)

        storage.append_record(DB_PATH, {
            "barcode": ean,
            "inventory_number": inv,
            "name": name,
            "description": desc,
            "date_glued": date_str,
            "status": storage.DEFAULT_STATUS,
        })

        # превью в интерфейсе (масштабируем для наглядности)
        preview = image.resize((image.width * 2, image.height * 2))
        self._preview_photo = ImageTk.PhotoImage(preview)
        self.preview_canvas.configure(image=self._preview_photo)

        self.label_result.configure(
            text=f"Штрих-код: {ean}\nНаклейка сохранена:\n{path}"
        )

        self.entry_inv.delete(0, "end")
        self.entry_name.delete(0, "end")
        self.text_desc.delete("1.0", "end")

    # ------------------------------------------------------------------
    # Вкладка 2: действия по штрих-коду (списание/передача/установка)
    # ------------------------------------------------------------------
    def _build_tab_actions(self):
        frame = self.tab_actions
        pad = {"padx": 6, "pady": 4}

        top = ttk.Frame(frame)
        top.pack(fill="x", padx=10, pady=8)

        ttk.Label(top, text="Введите номер штрих-кода:").grid(row=0, column=0, sticky="w", **pad)
        self.entry_barcode = ttk.Entry(top, width=24)
        self.entry_barcode.grid(row=0, column=1, **pad)
        self.entry_barcode.bind("<Return>", lambda e: self._add_to_queue())

        ttk.Label(top, text="Описание (для этого объекта в этом акте):").grid(
            row=1, column=0, sticky="w", **pad)
        self.entry_item_description = ttk.Entry(top, width=40)
        self.entry_item_description.grid(row=1, column=1, sticky="w", **pad)

        ttk.Button(top, text="Добавить в список", command=self._add_to_queue).grid(
            row=0, column=2, rowspan=2, **pad)

        ttk.Label(top, text="Действие:").grid(row=2, column=0, sticky="w", **pad)
        self.combo_action = ttk.Combobox(top, values=ACTIONS, state="readonly", width=20)
        self.combo_action.current(0)
        self.combo_action.grid(row=2, column=1, sticky="w", **pad)

        mid = ttk.Frame(frame)
        mid.pack(fill="both", expand=True, padx=10, pady=4)

        ttk.Label(mid, text="Объекты для документа:").pack(anchor="w")
        self.listbox = tk.Listbox(mid, height=10)
        self.listbox.pack(fill="both", expand=True, pady=4)

        ttk.Button(mid, text="Удалить выделенное", command=self._remove_selected).pack(anchor="w")

        bottom = ttk.LabelFrame(frame, text="Данные для документа")
        bottom.pack(fill="x", padx=10, pady=8)

        ttk.Label(bottom, text="Номер документа").grid(row=0, column=0, sticky="w", **pad)
        self.entry_docnum = ttk.Entry(bottom, width=20)
        self.entry_docnum.grid(row=0, column=1, sticky="w", **pad)

        ttk.Button(bottom, text="Сформировать документ", command=self._generate_document).grid(
            row=1, column=0, columnspan=2, pady=10)

    def _add_to_queue(self):
        bc = self.entry_barcode.get().strip()
        if not bc:
            return
        record = storage.find_by_barcode(DB_PATH, bc)
        if not record:
            messagebox.showerror("Не найдено", f"Штрих-код {bc} отсутствует в базе.")
            return
        if any(r["barcode"] == record["barcode"] for r in self.queue):
            messagebox.showinfo("Уже в списке", "Этот объект уже добавлен.")
            self.entry_barcode.delete(0, "end")
            self.entry_barcode.focus()
            return

        # копия записи, чтобы не менять исходную базу — описание для акта своё
        item = dict(record)
        custom_description = self.entry_item_description.get().strip()
        if custom_description:
            item["description"] = custom_description

        self.queue.append(item)
        self.listbox.insert(
            "end",
            f'{item["barcode"]}  |  {item["inventory_number"]}  |  {item["name"]}  |  {item["description"]}'
        )
        self.entry_barcode.delete(0, "end")
        self.entry_item_description.delete(0, "end")
        self.entry_barcode.focus()

    def _remove_selected(self):
        sel = list(self.listbox.curselection())
        for idx in reversed(sel):
            self.listbox.delete(idx)
            del self.queue[idx]

    def _generate_document(self):
        if not self.queue:
            messagebox.showerror("Ошибка", "Список объектов пуст. Добавьте хотя бы один штрих-код.")
            return

        action = self.combo_action.get()
        if action not in ACTIONS:
            messagebox.showerror("Ошибка", "Выберите действие.")
            return

        doc_number = self.entry_docnum.get().strip()
        date_str = datetime.date.today().strftime("%d.%m.%Y")

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_number = doc_number.replace("/", "-").replace("\\", "-") if doc_number else "б-н"
        filename = f"{action}_{safe_number}_{timestamp}.docx"
        path = os.path.join(DOCS_DIR, filename)

        try:
            documents.create_act_docx(
                action_type=action,
                doc_number=doc_number or "-",
                date_str=date_str,
                items=self.queue,
                output_path=path,
            )
        except Exception as exc:
            messagebox.showerror("Ошибка формирования документа", str(exc))
            return

        updated = storage.update_status(
            DB_PATH, [r["barcode"] for r in self.queue], STATUS_BY_ACTION[action]
        )
        try:
            documents.create_act_docx(
                action_type=action,
                doc_number=doc_number or "-",
                date_str=date_str,
                items=self.queue,
                output_path=path,
            )
        except Exception as exc:
            messagebox.showerror("Ошибка формирования документа", str(exc))
            return

        open_file(path)   # ← открывает документ сразу после сохранения

        updated = storage.update_status(
            DB_PATH, [r["barcode"] for r in self.queue], STATUS_BY_ACTION[action]
        )
        messagebox.showinfo(
            "Готово",
            f"Документ сохранён:\n{path}\n\nОбновлено записей в базе: {updated}"
        )

    # ------------------------------------------------------------------
    # Вкладка 3: проверка базы
    # ------------------------------------------------------------------
    def _build_tab_verify(self):
        frame = self.tab_verify
        ttk.Button(frame, text="Запустить проверку базы", command=self._run_verify).pack(
            anchor="w", padx=10, pady=10)

        self.verify_text = scrolledtext.ScrolledText(frame, wrap="word")
        self.verify_text.pack(fill="both", expand=True, padx=10, pady=10)

    def _run_verify(self):
        report = storage.verify_database(DB_PATH)

        lines = []
        lines.append(f"Всего записей в базе: {report['total']}")
        lines.append("")

        if report["duplicate_barcodes"]:
            lines.append("⚠ Повторяющиеся штрих-коды:")
            for bc in report["duplicate_barcodes"]:
                lines.append(f"   - {bc}")
        else:
            lines.append("✔ Повторяющихся штрих-кодов не найдено.")
        lines.append("")

        if report["duplicate_inventory_numbers"]:
            lines.append("⚠ Повторяющиеся инвентарные номера:")
            for inv in report["duplicate_inventory_numbers"]:
                lines.append(f"   - {inv}")
        else:
            lines.append("✔ Повторяющихся инвентарных номеров не найдено.")
        lines.append("")

        if report["invalid_checksum"]:
            lines.append("⚠ Штрих-коды с неверной контрольной суммой EAN13:")
            for bc in report["invalid_checksum"]:
                lines.append(f"   - {bc}")
        else:
            lines.append("✔ Все контрольные суммы EAN13 корректны.")
        lines.append("")

        if report["missing_fields"]:
            lines.append("⚠ Строки с незаполненными обязательными полями:")
            for row_num, missing in report["missing_fields"]:
                lines.append(f"   - строка {row_num}: не заполнено — {', '.join(missing)}")
        else:
            lines.append("✔ Все обязательные поля заполнены.")

        self.verify_text.delete("1.0", "end")
        self.verify_text.insert("1.0", "\n".join(lines))


if __name__ == "__main__":
    app = App()
    app.mainloop()
