import tkinter as tk
from tkinter import filedialog
import os
import cv2
import numpy as np
import openpyxl
from concurrent.futures import ThreadPoolExecutor, as_completed

# Функция обработки блока изображения
def block_processing(block):
    gray = cv2.cvtColor(block, cv2.COLOR_BGR2GRAY)
    _, thresholded = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    star_count = len(contours)
    star_brightness = []

    for contour in contours:
        mask = np.zeros(gray.shape, dtype=np.uint8)
        cv2.drawContours(mask, [contour], -1, 255, thickness=cv2.FILLED)
        mean_brightness = cv2.mean(block, mask=mask)[0]
        star_brightness.append(mean_brightness)

    return star_count, np.mean(star_brightness) if star_brightness else 0, contours

# Функция обработки блока изображения в многопоточной среде
def image_block_processing(image, block_size, i, j, processed_chunks_path):
    block = image[i:i + block_size[1], j:j + block_size[0]]
    star_count, average_brightness, contours = block_processing(block)

    processed_chunk_path = os.path.join(processed_chunks_path, f"block_{i}_{j}.jpg")
    cv2.drawContours(block, contours, -1, (255, 0, 0), 2)
    cv2.imwrite(processed_chunk_path, block)

    return star_count, average_brightness, contours

# Функция обработки всего изображения
def image_processing(image_path, block_size, processed_chunks_folder, processed_images_folder):
    results = []
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    height, width, _ = image.shape

    processed_chunks_path = os.path.join(processed_chunks_folder, os.path.basename(image_path))
    os.makedirs(processed_chunks_path, exist_ok=True)

    with ThreadPoolExecutor() as executor:
        futures = []

        for i in range(0, height, block_size[1]):
            for j in range(0, width, block_size[0]):
                future = executor.submit(image_block_processing, image, block_size, i, j, processed_chunks_path)
                futures.append(future)

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    processed_image_path = os.path.join(processed_images_folder, os.path.basename(image_path))
    cv2.imwrite(processed_image_path, image)

    return results

# Функция обработки всех изображений в выбранной папке
def images_processing():
    folder_path = selected_folder_path_var.get()
    image_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.jpg') or f.endswith('.png')]

    block_size = (256, 160)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['File Name', 'Star Count', 'Average Brightness'])

    processed_chunks_folder = "output_chunks"
    processed_images_folder = "output_images"
    os.makedirs(processed_chunks_folder, exist_ok=True)
    os.makedirs(processed_images_folder, exist_ok=True)

    with ThreadPoolExecutor() as executor:
        futures = []

        for image_path in image_files:
            future = executor.submit(image_processing, image_path, block_size, processed_chunks_folder,
                                     processed_images_folder)
            futures.append((image_path, future))

        for image_path, future in futures:
            results = future.result()

            total_star_count = sum(result[0] for result in results)
            avg_brightness = sum(result[1] for result in results) / len(results)

            ws.append([os.path.basename(image_path), total_star_count, avg_brightness])

    wb.save(os.path.join(processed_images_folder, 'stars_analysis.xlsx'))
    print('All results saved in stars_analysis.xlsx')

# Функция для выбора папки с изображениями
def select_folder():
    folder_path = filedialog.askdirectory()
    selected_folder_path_var.set(folder_path)

# Создание папок для сохранения обработанных данных
output_folder_chunks = "output_chunks"
output_folder_images = "output_images"
os.makedirs(output_folder_chunks, exist_ok=True)
os.makedirs(output_folder_images, exist_ok=True)

# Создание главного окна Tkinter
root = tk.Tk()
root.title("Stars Analysis on Images")

# Установка размера шрифта для главного окна
root.option_add('*Font', 'Arial 12')

# Установка цвета фона для главного окна
root.configure(bg='lightgray')

selected_folder_path_var = tk.StringVar()

# Label для текста
label_text = tk.Label(root, text="Select the folder with images:", bg='lightgray')
label_text.config(font=('Arial', 14))  # Изменение размера шрифта для Label
label_text.pack()

# Entry для ввода текста
entry = tk.Entry(root, textvariable=selected_folder_path_var, width=40, font=('Arial', 12))  # Изменение размера шрифта для Entry
entry.pack()

# Button для вызова функции выбора папки
button_browse = tk.Button(root, text="Browse", command=select_folder, bg='gray', fg='white')
button_browse.config(font=('Arial', 12))  # Изменение размера шрифта для Button
button_browse.pack()

# Button для вызова функции анализа изображений
button_analyze = tk.Button(root, text="Analyze Images", command=images_processing, bg='blue', fg='white')
button_analyze.config(font=('Arial', 12))  # Изменение размера шрифта для Button
button_analyze.pack()

# Запуск главного цикла Tkinter
root.mainloop()
