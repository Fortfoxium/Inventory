from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from bar_generator import *
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import barcode 
from barcode.writer import ImageWriter
from barcode.writer import SVGWriter
import random
import os

def exit_app():
    window.destroy()
    print('Выполняется закрытия инициированное пользователем.')
    
def window_write_down():
    window_wd = Toplevel(window)
    window_wd.title("Списание")
    window_wd.geometry("250x200")
    frame = ttk.Frame(window_wd,borderwidth=1, relief=SOLID, padding=[8, 10])
    name_label = ttk.Label(frame, text="Введите имя")
    name_label.pack(anchor=NW)
 
    name_entry = ttk.Entry(frame)
    name_entry.pack(anchor=NW)
 
    frame.pack(anchor=NW, fill=X, padx=5, pady=5)

def window_generate_code():

    def on_generate():
        """Обработчик нажатия кнопки: берёт текст из Entry и вызывает генерацию."""
        user_text = inv_entry.get().strip()      # Получаем введённый текст, убираем лишние пробелы
        if not user_text:
            messagebox.showwarning("Внимание", "Введите текст для подписи под штрихкодом!")
            return

        try:
            saved_file = generate_barcode_and_save(user_text)
            messagebox.showinfo("Готово", f"Штрихкод сохранён в файл:\n{saved_file}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать штрихкод:\n{e}")
    win_gc = Toplevel(window)
    win_gc.title("Генерация штрих-кодов")
    win_gc.geometry("250x200")
    
    frame = ttk.Frame(win_gc,borderwidth=1, height=100, relief=SOLID, padding=[8, 10])
    name_label = ttk.Label(frame, text="Введите инвентарный номер:")
    name_label.pack(anchor=N)
 
    inv_entry = ttk.Entry(frame)
    inv_entry.pack(anchor=N)

    btn=ttk.Button(frame, text="Присвоение штрих-кода", command=(on_generate))
    btn.pack(anchor=NW)

    
    frame.pack(anchor=N, fill=X, padx=5, pady=5)
    generate_barcode_and_save()

    

   


    



    
"""Основное тело программы:"""

window = Tk()
window.title("Inventory")
window.geometry("600x50+600+300")

welcome = Label(text="Добро пожаловать в программу инвентаризации \"Inventory\"!")
welcome.pack()

work_menu = Menu()
work_menu.add_command(label="Выход", command=exit_app)
work_menu.add_command(label="Списание", command=window_write_down)
work_menu.add_command(label="Добавление", command=window_generate_code)

window.config(menu=work_menu)
window.mainloop()

