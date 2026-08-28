# -*- coding: utf-8 -*-
"""
Модуль работы с базой инвентарных объектов.

База хранится в обычном CSV-файле (по умолчанию inventory.csv), кодировка
utf-8-sig — чтобы файл корректно открывался в Excel с кириллицей.

Столбцы:
    barcode          — полный EAN13 штрих-код (13 цифр)
    inventory_number — инвентарный номер объекта
    name             — наименование объекта
    description      — краткое описание
    date_glued       — дата оклейки штрих-кода (ДД.ММ.ГГГГ)
    status           — текущий статус ("На складе", "Списан", "Передан", "Установлен")
"""

import csv
import os

FIELDS = ["barcode", "inventory_number", "name", "description", "date_glued", "status"]

DEFAULT_STATUS = "На складе"


def ensure_db(path: str) -> None:
    """Создаёт файл базы с заголовком, если он ещё не существует."""
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS, delimiter=";")
            writer.writeheader()


def read_all(path: str):
    """Возвращает список записей (list[dict])."""
    ensure_db(path)
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f, delimiter=";")
        return [row for row in reader]


def write_all(path: str, rows) -> None:
    """Полностью перезаписывает файл базы переданным списком записей."""
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, delimiter=";")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in FIELDS})


def append_record(path: str, record: dict) -> None:
    ensure_db(path)
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, delimiter=";")
        writer.writerow({k: record.get(k, "") for k in FIELDS})


def find_by_barcode(path: str, barcode: str):
    barcode = barcode.strip()
    for row in read_all(path):
        if row.get("barcode", "").strip() == barcode:
            return row
    return None


def update_status(path: str, barcodes, new_status: str) -> int:
    """Обновляет статус у записей с указанными штрих-кодами. Возвращает число обновлённых записей."""
    barcodes = set(b.strip() for b in barcodes)
    rows = read_all(path)
    updated = 0
    for row in rows:
        if row.get("barcode", "").strip() in barcodes:
            row["status"] = new_status
            updated += 1
    write_all(path, rows)
    return updated


def _ean13_checksum_ok(code: str) -> bool:
    """Проверяет контрольную цифру EAN13."""
    if len(code) != 13 or not code.isdigit():
        return False
    digits = [int(c) for c in code[:12]]
    total = sum(d * (1 if i % 2 == 0 else 3) for i, d in enumerate(digits))
    check = (10 - total % 10) % 10
    return check == int(code[12])


def verify_database(path: str) -> dict:
    """
    Проверяет базу и возвращает словарь с найденными проблемами:
        duplicate_barcodes, duplicate_inventory_numbers,
        missing_fields (список строк с указанием, чего не хватает),
        invalid_checksum (штрих-коды с неверной контрольной суммой),
        total — общее количество записей
    """
    rows = read_all(path)

    seen_barcodes = {}
    seen_inv = {}
    duplicate_barcodes = set()
    duplicate_inventory_numbers = set()
    missing_fields = []
    invalid_checksum = []

    for i, row in enumerate(rows, start=2):  # строка 1 — заголовок
        bc = row.get("barcode", "").strip()
        inv = row.get("inventory_number", "").strip()
        name = row.get("name", "").strip()

        if bc:
            if bc in seen_barcodes:
                duplicate_barcodes.add(bc)
            seen_barcodes[bc] = i
            if not _ean13_checksum_ok(bc):
                invalid_checksum.append(bc)

        if inv:
            if inv in seen_inv:
                duplicate_inventory_numbers.add(inv)
            seen_inv[inv] = i

        missing = []
        if not bc:
            missing.append("штрих-код")
        if not inv:
            missing.append("инвентарный номер")
        if not name:
            missing.append("наименование")
        if missing:
            missing_fields.append((i, missing))

    return {
        "total": len(rows),
        "duplicate_barcodes": sorted(duplicate_barcodes),
        "duplicate_inventory_numbers": sorted(duplicate_inventory_numbers),
        "missing_fields": missing_fields,
        "invalid_checksum": sorted(invalid_checksum),
    }
