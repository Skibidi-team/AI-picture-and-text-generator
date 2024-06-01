import json
import time
import requests
import base64
from tkinter import Tk, Label, Entry, Button, messagebox, StringVar, OptionMenu, colorchooser, Frame, Scale, LEFT, RIGHT, TOP, W, E, N, S, BooleanVar, Checkbutton
import subprocess
import os
from PIL import Image, ImageDraw, ImageFont

class Text2ImageAPI:
    def __init__(self, url, api_key, secret_key):
        self.URL = url
        self.AUTH_HEADERS = {
            'X-Key': f'Key {api_key}',
            'X-Secret': f'Secret {secret_key}',
        }

    def get_model(self):
        response = requests.get(self.URL + 'key/api/v1/models', headers=self.AUTH_HEADERS)
        data = response.json()
        return data[0]['id']

    def generate(self, prompt, model, images=1, width=512, height=512):
        params = {
            "type": "GENERATE",
            "style": "UHD",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": f"{prompt}"
            }
        }
        data = {
            'model_id': (None, model),
            'params': (None, json.dumps(params), 'application/json')
        }
        response = requests.post(self.URL + 'key/api/v1/text2image/run', headers=self.AUTH_HEADERS, files=data)
        data = response.json()
        return data['uuid']

    def check_generation(self, request_id, attempts=10, delay=10):
        while attempts > 0:
            response = requests.get(self.URL + 'key/api/v1/text2image/status/' + request_id, headers=self.AUTH_HEADERS)
            data = response.json()
            if data['status'] == 'DONE':
                return data['images']
            attempts -= 1
            time.sleep(delay)

def hex_to_rgba(hex_color, alpha=128):
    hex_color = hex_color.lstrip('#')
    lv = len(hex_color)
    return tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3)) + (alpha,)

def wrap_text(text, draw, font, max_width):
    lines = []
    words = text.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines

def generate_image():
    prompt = prompt_entry.get()

    size_option = size_var.get()
    if size_option == "Баннер (1000 x 434)":
        width, height = 1000, 434
    elif size_option == "Скринсейвер (1024 x 720)":
        width, height = 1024, 720
    elif size_option == "Лист А4 (1240 х 1754)":
        width, height = 1240, 1754
    else:  # Выбор вручную
        width = int(width_entry.get())
        height = int(height_entry.get())

    uuid = api.generate(prompt, model_id, width=width, height=height)
    images = api.check_generation(uuid)

    if images:
        image_base64 = images[0]
        image_data = base64.b64decode(image_base64)
        image_filename = f"{prompt}.jpg"
        with open(image_filename, "wb") as file:
            file.write(image_data)
            add_text_to_image(image_filename)
            if add_logo_var.get():
                overlay_corner_image(image_filename)
            messagebox.showinfo("Успех", f"Изображение сгенерировано, текст добавлен и изображение в углу наложено успешно: {image_filename}")
    else:
        messagebox.showerror("Ошибка", "Не удалось сгенерировать изображение.")

def add_text_to_image(image_filename):
    text = text_entry.get()
    text_color = color_var.get()
    background_color = bg_color_var.get()
    text_size = int(size_scale.get())
    padding = 10  # Отступы вокруг текста

    img = Image.open(image_filename)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", text_size)

    max_text_width = img.width - 2 * padding

    lines = wrap_text(text, draw, font, max_text_width)
    line_height = draw.textbbox((0, 0), 'hg', font=font)[3] - draw.textbbox((0, 0), 'hg', font=font)[1]
    text_height = line_height * len(lines)
    text_width = max(draw.textbbox((0, 0), line, font=font)[2] for line in lines)

    # Определяем позицию текста в зависимости от выбранной опции
    if position_var.get() == "Сверху":
        pos_x = (img.width - text_width) / 2
        pos_y = padding
    elif position_var.get() == "В центре":
        pos_x = (img.width - text_width) / 2
        pos_y = (img.height - text_height) / 2
    else:  # position_var.get() == "Снизу"
        pos_x = (img.width - text_width) / 2
        pos_y = img.height - text_height - padding

    # Draw semi-transparent background with padding
    background = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw_background = ImageDraw.Draw(background)
    rgba_background_color = hex_to_rgba(background_color)
    draw_background.rectangle((pos_x - padding, pos_y - padding, pos_x + text_width + padding, pos_y + text_height + padding),
                              fill=rgba_background_color)
    img = Image.alpha_composite(img.convert('RGBA'), background)

    draw = ImageDraw.Draw(img)
    y = pos_y
    for line in lines:
        draw.text((pos_x, y), line, font=font, fill=text_color)
        y += line_height

    img.save(image_filename.replace(".jpg", "_with_text.png"))

def overlay_corner_image(image_filename):
    main_image = Image.open(image_filename.replace(".jpg", "_with_text.png")).convert("RGBA")
    corner_image = Image.open("C:\\Users\\korot\\PycharmProjects\\pythonProject\\gerbbbb.png").convert("RGBA")

    # Resize corner image to fit within the top left corner
    corner_image.thumbnail((main_image.width // 3, main_image.height // 3))

    # Overlay corner image onto main image
    main_image.paste(corner_image, (0, 0), corner_image)
    main_image.save(image_filename.replace(".jpg", "_with_text.png"))

def open_image_folder():
    image_folder = os.path.dirname(os.path.realpath(__file__))
    subprocess.Popen(f'explorer {image_folder}')

def choose_color():
    color = colorchooser.askcolor()[1]
    if color:
        color_var.set(color)

def choose_bg_color():
    color = colorchooser.askcolor()[1]
    if color:
        bg_color_var.set(color)

def on_size_option_change(*args):
    if size_var.get() == "Выбор вручную":
        custom_size_frame.pack(pady=5)
    else:
        custom_size_frame.pack_forget()

# Создаем основное окно Tkinter
root = Tk()
root.title("Генератор изображений с текстом")
root.geometry("1000x600")

api = Text2ImageAPI('https://api-key.fusionbrain.ai/', 'C486A015C59709FBA8956C7933FF7018',
                    '29E773B8206CEF407DF19F3E5852E480')
model_id = api.get_model()

# Создаем и размещаем элементы интерфейса с улучшенным дизайном

frame_prompt_text = Frame(root)
frame_prompt_text.pack(pady=10)

# Добавление метки и поля для ввода запроса
Label(frame_prompt_text, text="Введите запрос:", font=("Arial", 12)).grid(row=0, column=0, padx=5, sticky=W)
prompt_entry = Entry(frame_prompt_text, font=("Arial", 12), width=40, # Increased width to 40
                     justify="left",   # Align text to the left
                     bd=1,   # Border width
                     relief="solid",  # Border style
                     insertborderwidth=2,  # Width of the insertion cursor's border
                     insertbackground="black",  # Color of the insertion cursor
                     selectbackground="lightgray",  # Background color when selected
                     selectforeground="black")  # Text color when selected
prompt_entry.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")  # Expanded height

# Добавление метки и поля для ввода текста
Label(frame_prompt_text, text="Введите текст для добавления:", font=("Arial", 12)).grid(row=0, column=1, padx=5, sticky=W)
text_entry = Entry(frame_prompt_text, font=("Arial", 12), width=40,  # Increased width to 40
                   justify="left",   # Align text to the left
                   bd=1,   # Border width
                   relief="solid",  # Border style
                   insertborderwidth=2,  # Width of the insertion cursor's border
                   insertbackground="black",  # Color of the insertion cursor
                   selectbackground="lightgray",  # Background color when selected
                   selectforeground="black",  # Text color when selected
                   )
text_entry.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")  # Expanded height

# Выбор размера изображения
size_var = StringVar(root)
size_var.set("Выбор размера изображения")
size_var.trace("w", on_size_option_change)
Label(root, text="Выберите размер изображения:", font=("Arial", 12)).pack()
size_menu = OptionMenu(root, size_var, "Баннер (1000 x 434)", "Скринсейвер (1024 x 720)", "Лист А4 (1240 х 1754)",
                       "Выбор вручную")
size_menu.pack(pady=5)

custom_size_frame = Frame(root)
Label(custom_size_frame, text="Введите ширину изображения:", font=("Arial", 12)).pack()
width_entry = Entry(custom_size_frame, font=("Arial", 12))
width_entry.pack(pady=5)

Label(custom_size_frame, text="Введите высоту изображения:", font=("Arial", 12)).pack()
height_entry = Entry(custom_size_frame, font=("Arial", 12))
height_entry.pack(pady=5)

# Ползунок выбора размера текста
Label(root, text="Выберите размер текста:", font=("Arial", 12)).pack()
size_scale = Scale(root, from_=10, to_=100, orient="horizontal")
size_scale.set(20)
size_scale.pack(pady=5)

# Выберите цвет текста и Выберите цвет подложки
frame_colors = Frame(root)
frame_colors.pack(pady=10)

color_var = StringVar()
color_var.set("#FFFFFF")
color_button = Button(frame_colors, text="Выбрать цвет текста", command=choose_color)
color_button.pack(side=LEFT, padx=5)

bg_color_var = StringVar()
bg_color_var.set("#000000")
bg_color_button = Button(frame_colors, text="Выбрать цвет подложки", command=choose_bg_color)
bg_color_button.pack(side=LEFT, padx=5)

# Выберите позицию текста
Label(root, text="Выберите позицию текста:", font=("Arial", 12)).pack()
position_var = StringVar(root)
position_var.set("Сверху")
position_menu = OptionMenu(root, position_var, "Сверху", "В центре", "Снизу")
position_menu.pack(pady=3)

# Добавление опции выбора логотипа
add_logo_var = BooleanVar()
add_logo_var.set(True)
Checkbutton(root, text="Добавить логотип ЦБ", variable=add_logo_var).pack(pady=5)

# Сгенерировать изображение и Открыть папку с изображениями
frame_buttons = Frame(root)
frame_buttons.pack(pady=10)

generate_button = Button(frame_buttons, text="Сгенерировать изображение", command=generate_image, font=("Arial", 12),
                         bg="green", fg="white", relief="raised")
generate_button.pack(side=LEFT, padx=5)

open_folder_button = Button(frame_buttons, text="Открыть папку с изображениями", command=open_image_folder, font=("Arial", 12),
                            bg="blue", fg="white", relief="raised")
open_folder_button.pack(side=LEFT, padx=5)

root.mainloop()