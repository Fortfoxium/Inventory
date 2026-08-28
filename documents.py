# -*- coding: utf-8 -*-
"""
Формирование документов (актов) на списание / передачу / установку
объектов на основе списка отсканированных/введённых штрих-кодов.
"""

from docx import Document
from docx.shared import Cm, Pt, Mm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

ACTION_TITLES = {
    "Списание": "АКТ СПИСАНИЯ",
    "Передача": "АКТ ПЕРЕДАЧИ",
    "Установка": "АКТ УСТАНОВКИ",
}


def create_act_docx(action_type: str, doc_number: str, date_str: str,
                      items: list, output_path: str) -> None:
    """
    action_type — одно из "Списание", "Передача", "Установка"
    items — список dict с ключами: inventory_number, name, description, barcode
    """
    title = ACTION_TITLES.get(action_type, f"АКТ ({action_type})")

    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)

    # Заголовок
    h = doc.add_paragraph()
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = h.add_run(title)
    run.bold = True
    run.font.size = Pt(16)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run(f"№___ {doc_number} от {date_str}")

    doc.add_paragraph()

    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Mm(10)
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.add_run("Комиссия в составе: председателя комиссии Силанова А.А. – Заместителя ген.директора; членов комиссии: Кисилевой Л.М. – экономиста, Батуро А.П - бухгалтера, Полищук Р.Ю..-начальник ИТО, составила настоящий Акт в том, что на __________________________________ были установлены:")
    

    doc.add_paragraph()

    # Таблица объектов
    table = doc.add_table(rows=1, cols=5)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    widths = [Cm(1.2), Cm(3.2), Cm(5.0), Cm(5.0), Cm(3.4)]
    headers = ["№ п/п", "Инв. номер", "Наименование", "Количество, шт", "Примечание"]

    hdr_cells = table.rows[0].cells
    for i, text in enumerate(headers):
        hdr_cells[i].text = text
        for p_ in hdr_cells[i].paragraphs:
            for r in p_.runs:
                r.bold = True
        table.columns[i].width = widths[i]

    for idx, item in enumerate(items, start=1):
        row = table.add_row().cells
        row[0].text = str(idx)
        row[1].text = item.get("inventory_number", "")
        row[2].text = item.get("name", "")
        row[3].text = "-"
        row[4].text = item.get("description", "")
        for i, w in enumerate(widths):
            row[i].width = w

    doc.add_paragraph()
    doc.add_paragraph()

    sign = doc.add_paragraph()
    sign.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    

    sign.add_run("Председатель комиссии:						          Силанов А.А.\n")
    sign.add_run("Члены комиссии:         	                                                                      Киселева Л.М.\n")
    sign.add_run("               	                                                                                              Батуро А.П.\n")
    sign.add_run("               	                                                                                              Полищук Р.Ю.\n")

    doc.save(output_path)
