# -*- coding: utf-8 -*-
"""
Генерация уникальных штрих-кодов EAN13 и изображений наклеек для
термопринтера Xprinter XP-365B (наклейка 58 x 40 мм).
"""

import os
from PIL import Image, ImageDraw, ImageFont

import barcode
from barcode.writer import ImageWriter

# --- Настройки печати -----------------------------------------------------

# Разрешение принтера в точках на дюйм. У большинства этикеточных
# термопринтеров (в т.ч. XP-365B) это 203 dpi. Если наклейки печатаются
# со сдвигом/обрезкой — поменяйте это значение (уточните в характеристиках
# принтера или в настройках драйвера).
DPI = 203

LABEL_WIDTH_MM = 58
LABEL_HEIGHT_MM = 40

# Префикс для внутренних (не товарных) кодов. Диапазон 200-299 в стандарте
# EAN13 зарезервирован под внутреннее использование организаций и никогда
# не пересечётся с реальными товарными штрих-кодами.
PREFIX = "200"

COUNTER_FILE = "counter.txt"


def _mm_to_px(mm: float) -> int:
    return int(round(mm / 25.4 * DPI))


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    """Пытается найти шрифт с поддержкой кириллицы. При отсутствии — предупреждает."""
    candidates = [
        "arial.ttf", "Arial.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    # Крайний случай — стандартный растровый шрифт Pillow. Кириллицу
    # он не поддерживает, поэтому лучше положить рядом со скриптом файл
    # шрифта (например DejaVuSans.ttf) и добавить его путь в candidates выше.
    return ImageFont.load_default()


def next_sequence_number(base_dir: str) -> int:
    """Возвращает следующий порядковый номер и сохраняет счётчик на диск."""
    counter_path = os.path.join(base_dir, COUNTER_FILE)
    n = 1
    if os.path.exists(counter_path):
        with open(counter_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content.isdigit():
                n = int(content) + 1
    with open(counter_path, "w", encoding="utf-8") as f:
        f.write(str(n))
    return n


def generate_ean13(base_dir: str) -> str:
    """Генерирует новый уникальный 13-значный код EAN13 (с контрольной цифрой)."""
    seq = next_sequence_number(base_dir)
    # PREFIX (3 цифры) + порядковый номер, дополненный нулями до 9 цифр = 12 цифр
    code12 = f"{PREFIX}{seq:09d}"
    ean = barcode.get("ean13", code12, writer=ImageWriter())
    return ean.get_fullcode()


def create_label_image(ean_code: str, inventory_number: str, name: str,
                        description: str, date_str: str) -> Image.Image:
    """Формирует готовое изображение наклейки 58x40мм для печати на термопринтере."""
    width_px = _mm_to_px(LABEL_WIDTH_MM)
    height_px = _mm_to_px(LABEL_HEIGHT_MM)

    label = Image.new("RGB", (width_px, height_px), "white")
    draw = ImageDraw.Draw(label)

    margin = _mm_to_px(1.5)

    # Шрифты
    font_small = _load_font(_mm_to_px(2.6))
    font_bold = _load_font(_mm_to_px(3.0))

    y = margin

    # Наименование (может переноситься на 2 строки)
    name_lines = _wrap_text(draw, name, font_bold, width_px - 2 * margin, max_lines=2)
    for line in name_lines:
        draw.text((margin, y), line, font=font_bold, fill="black")
        y += font_bold.size + 2

    # Инвентарный номер
    draw.text((margin, y), f"Инв. № {inventory_number}", font=font_small, fill="black")
    y += font_small.size + 2

    # Описание (1 строка, обрезается если не помещается)
    if description:
        desc_lines = _wrap_text(draw, description, font_small, width_px - 2 * margin, max_lines=1)
        if desc_lines:
            draw.text((margin, y), desc_lines[0], font=font_small, fill="black")
            y += font_small.size + 2

    # Штрих-код — рисуем в оставшейся нижней части наклейки
    barcode_area_height = height_px - y - _mm_to_px(4.5)  # оставляем место под дату
    if barcode_area_height < _mm_to_px(10):
        barcode_area_height = _mm_to_px(10)

    # Текст цифр под штрих-кодом рисуем сами (шрифтом с кириллицей/устойчивым
    # к масштабированию), поэтому у самой библиотеки текст отключаем —
    # иначе при неравномерном масштабировании цифры "наезжают" на полосы.
    ean = barcode.get(
        "ean13", ean_code[:12], writer=ImageWriter()
    )
    bc_options = {
        "module_width": 0.28,
        "module_height": barcode_area_height / DPI * 25.4 * 0.5,
        "quiet_zone": 1.0,
        "dpi": DPI,
        "write_text": False,
    }
    bc_img = ean.render(bc_options)

    # Вписываем штрих-код по ширине наклейки, сохраняя пропорции
    date_text = f"Оклеено: {date_str}"
    reserved_bottom = font_small.size + 4  # место под дату
    digits_height = font_small.size + 2    # место под цифры кода под полосами
    max_bc_height = height_px - y - reserved_bottom - digits_height - 2
    if max_bc_height < _mm_to_px(8):
        max_bc_height = _mm_to_px(8)

    scale = min((width_px - 2 * margin) / bc_img.width, max_bc_height / bc_img.height)
    new_size = (max(1, int(bc_img.width * scale)), max(1, int(bc_img.height * scale)))
    bc_img = bc_img.resize(new_size, Image.LANCZOS)

    bc_x = margin + (width_px - 2 * margin - bc_img.width) // 2
    label.paste(bc_img, (bc_x, y))
    y += bc_img.height + 1

    # Цифры штрих-кода под полосами, по центру
    digits_bbox = draw.textbbox((0, 0), ean_code, font=font_small)
    digits_w = digits_bbox[2] - digits_bbox[0]
    draw.text((margin + (width_px - 2 * margin - digits_w) // 2, y), ean_code,
               font=font_small, fill="black")
    y += digits_height

    # Дата оклейки — внизу наклейки
    draw.text((margin, height_px - font_small.size - 2), date_text, font=font_small, fill="black")

    return label


def _wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, max_lines: int):
    """Простой перенос текста по ширине в пикселях. Обрезает лишнее с многоточием."""
    if not text:
        return []
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
            if len(lines) == max_lines:
                break
    if current and len(lines) < max_lines:
        lines.append(current)

    if len(lines) > max_lines:
        lines = lines[:max_lines]

    # Если текст не поместился целиком — добавляем многоточие к последней строке
    fitted_words = sum(len(l.split()) for l in lines)
    if fitted_words < len(words) and lines:
        last = lines[-1]
        while True:
            trial = last + "…"
            bbox = draw.textbbox((0, 0), trial, font=font)
            if bbox[2] - bbox[0] <= max_width or not last:
                lines[-1] = trial
                break
            last = last[:-1]

    return lines


def save_label_image(image: Image.Image, path: str) -> None:
    image.save(path, dpi=(DPI, DPI))
