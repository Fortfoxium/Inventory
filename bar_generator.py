import os
import random
import barcode 
from barcode.writer import ImageWriter
from barcode.writer import SVGWriter
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def generate_barcode_and_save(input_string: str) -> str:
        os.makedirs("barcodes/", exist_ok=True)
        os.makedirs("database/", exist_ok=True)

        """
        Генерирует уникальный 12-значный код, создаёт его штрихкод (SVG) с подписью,
        равной input_string. Код записывается в db.txt, если он там отсутствовал.
        Возвращает имя сохранённого SVG-файла.
        """
        # 1. Генерация уникального 12-значного числа, не встречающегося в db.txt
        while True:
            # Случайное целое число от 0 до 999_999_999_999 включительно,
            # дополненное слева нулями до 12 цифр (например, '000000000123')
            candidate = str(random.randint(0, 999_999_999_999)).zfill(12)

            # Если файла db.txt нет, то считаем, что число уникально
            if not os.path.exists('database/db.txt'):
                break

            # Читаем все строки файла (каждая строка – одно число) и убираем символы переноса
            with open('database/db.txt', 'r', encoding='utf-8') as f:
                existing = f.read().splitlines()

            if candidate not in existing:
                break   # нашли уникальное число, выходим из цикла

        # 2. Записываем уникальное число в конец файла db.txt
        with open('database/db.txt', 'a', encoding='utf-8') as f:
            f.write(candidate + '\n')
            
        fp = BytesIO()
        font = ImageFont.truetype("arial.ttf", size=12)
        filename = input_string
        #code128 = (barcode.get('code128', candidate, text ='font_size', writer=ImageWriter())).write(fp)
        code128 = barcode.get('code128', candidate, writer=ImageWriter())
        code128.save(filename, options={'font_size': 6})
        
        image = Image.open(filename+".png")
        width, height = image.size
        image = image.crop((0, 0, width, height+35))
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, height, width, height+50), fill='white')
        #draw.rectangle((0, 0, 100, height), fill='white')
        draw.text((25, height), input_string, fill='black', font=font)
        image.save("barcodes/"+input_string+".png")

        # 3. Создаём штрихкод в формате SVG
        # Тип штрихкода – Code128 (поддерживает цифры и некоторые символы)
        # В качестве данных кодируем наше 12-значное число
        #code128 = barcode.get('code128', candidate, writer=ImageWriter())

        # Имя файла будет состоять из префикса и самого числа (безопасно для файловой системы)
        #filename = input_string
       
        # Сохраняем SVG, передавая в опциях кастомный текст под штрихкодом
        #code128.save(filename, options={'font_size': 8})

        #draw = ImageDraw.Draw(Image.open(input_string+".png"))
        #draw.rectangle((0, height, width, height+100), fill='white')
        #draw.text((75, height + 18), "Ваш текст", fill='black', font=font)

        

        return filename