import cv2
import numpy as np
from PIL import Image
from pysstv.color import MartinM1, PD120, Robot36
import sounddevice as sd
import threading
import time
import tkinter as tk

# Variables globales
capture_interval = 0  # Valor en segundos; 0 significa que se usa el botón para capturar
capture_requested = False
current_frame = None
overlay_text = ""

# Captura de la imagen de la webcam
def capture_image():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if ret:
        return frame
    else:
        raise Exception("No se pudo capturar la imagen de la webcam")

# Añadir texto a la imagen
def add_text_to_image(image, text):
    font = cv2.FONT_HERSHEY_SIMPLEX
    bottom_left_corner_of_text = (10, image.shape[0] - 10)
    font_scale = 1
    font_color = (255, 255, 255)
    line_type = 2
    
    cv2.putText(image, text, bottom_left_corner_of_text, font, font_scale, font_color, line_type)
    return image

# Conversión de la imagen a SSTV MartinM1 (320x320)
def image_to_sstv_martinm1(image):
    # Convertir la imagen de OpenCV (numpy array) a PIL Image
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image)
    
    # Redimensionar la imagen a 320x320
    pil_image = pil_image.resize((320, 320), Image.LANCZOS)
    
    # Inicializar la imagen SSTV MartinM1
    samples_per_sec = 48000
    bits = 16
    sstv_image = MartinM1(pil_image, samples_per_sec=samples_per_sec, bits=bits)
    return sstv_image

# Conversión de la imagen a SSTV PD120 (640x496)
def image_to_sstv_pd120(image):
    # Convertir la imagen de OpenCV (numpy array) a PIL Image
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image)
    
    # Redimensionar la imagen a 640x496
    pil_image = pil_image.resize((640, 496), Image.LANCZOS)
    
    # Inicializar la imagen SSTV PD120
    samples_per_sec = 48000
    bits = 16
    sstv_image = PD120(pil_image, samples_per_sec=samples_per_sec, bits=bits)
    return sstv_image

# Conversión de la imagen a SSTV PD120 (640x496)
def image_to_sstv_robot36(image):
    # Convertir la imagen de OpenCV (numpy array) a PIL Image
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image)
    
    # Redimensionar la imagen a 640x496
    pil_image = pil_image.resize((320, 240), Image.LANCZOS)
    
    # Inicializar la imagen SSTV PD120
    samples_per_sec = 48000
    bits = 16
    sstv_image = Robot36(pil_image, samples_per_sec=samples_per_sec, bits=bits)
    return sstv_image

# Transmisión de la imagen por SSTV
def transmit_sstv(sstv_image):
    audio = list(sstv_image.gen_samples())  # Convertir el generador a una lista
    audio = np.array(audio, dtype=np.float32)  # Asegurarse de que el audio esté en formato float32
    sd.play(audio, sstv_image.samples_per_sec)
    sd.wait()

# Función para manejar la captura y transmisión
def capture_and_transmit():
    global overlay_text
    try:
        # Captura de la imagen
        image = current_frame
        
        # Añadir texto a la imagen
        image = add_text_to_image(image, overlay_text)
        
        # Conversión de la imagen a SSTV MartinM1 (320x320)
        #sstv_image = image_to_sstv_martinm1(image)
        
        # Opción 1: Conversión de la imagen a SSTV PD120 (640x496)
        # sstv_image = image_to_sstv_pd120(image)

        # Opción 2: Conversión de la imagen a SSTV robott36 (320x240)
        sstv_image = image_to_sstv_robot36(image)
        
        # Transmisión de la imagen por SSTV
        transmit_sstv(sstv_image)
        
        print("Imagen transmitida exitosamente por SSTV")
    except Exception as e:
        print(f"Error: {e}")

# Hilo para captura automática
def auto_capture():
    global capture_interval, capture_requested
    while True:
        if capture_interval > 0:
            time.sleep(capture_interval)
            capture_and_transmit()
        elif capture_requested:
            capture_and_transmit()
            capture_requested = False

# Configuración de la interfaz de la ventana
def setup_window():
    global capture_requested
    cv2.namedWindow("Webcam")
    
    def on_capture_button(event, x, y, flags, param):
        global capture_requested
        if event == cv2.EVENT_LBUTTONDOWN:
            capture_requested = True
    
    cv2.setMouseCallback("Webcam", on_capture_button)

# Función para actualizar el texto de superposición
def update_overlay_text(entry):
    global overlay_text
    overlay_text = entry.get()

# Función para iniciar la captura manual
def manual_capture():
    global capture_requested
    capture_requested = True

# Función para establecer el temporizador de captura
def set_capture_interval(entry):
    global capture_interval
    try:
        capture_interval = int(entry.get())
    except ValueError:
        capture_interval = 0

# Función principal para la visualización de la webcam
def display_webcam():
    global current_frame
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        current_frame = frame
        cv2.imshow("Webcam", frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # Presionar 'ESC' para salir
            break
    
    cap.release()
    cv2.destroyAllWindows()

# Configuración de la interfaz gráfica con Tkinter
def setup_gui():
    root = tk.Tk()
    root.title("SSTV Transmitter")
    
    # Ventana de texto
    text_label = tk.Label(root, text="Texto de superposición:")
    text_label.pack()
    text_entry = tk.Entry(root)
    text_entry.pack()
    text_entry.bind("<KeyRelease>", lambda event: update_overlay_text(text_entry))
    
    # Botón de captura manual
    capture_button = tk.Button(root, text="Capturar y Transmitir", command=manual_capture)
    capture_button.pack()
    
    # Entrada para el temporizador
    interval_label = tk.Label(root, text="Intervalo de captura (segundos, 0 para manual):")
    interval_label.pack()
    interval_entry = tk.Entry(root)
    interval_entry.pack()
    interval_entry.bind("<KeyRelease>", lambda event: set_capture_interval(interval_entry))
    
    # Iniciar la interfaz gráfica
    root.mainloop()

if __name__ == "__main__":
    # Iniciar hilo de captura automática
    capture_thread = threading.Thread(target=auto_capture, daemon=True)
    capture_thread.start()
    
    # Configurar la ventana de visualización
    setup_window()
    
    # Iniciar la interfaz gráfica en un hilo separado
    gui_thread = threading.Thread(target=setup_gui, daemon=True)
    gui_thread.start()
    
    # Mostrar la webcam
    display_webcam()
