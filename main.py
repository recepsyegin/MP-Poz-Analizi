import mediapipe as mp
import cv2
import numpy as np
import tkinter as tk
from tkinter import Label
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import pyttsx3
import threading
import time
import pandas as pd

# Multithreading,sesli yanit sonradan ekledik
def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

def start_speech_thread(text):
    threading.Thread(target=speak, args=(text,)).start()


mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

speech_enabled = True
posture_last_correct = None  # None başlangıç durumu, True veya False olacak
last_feedback_time = 0
feedback_interval = 5  # Saniye cinsinden geri bildirim aralığı

# Veri kaydı için değişkenler
data_records = []
data_file = "posture_data.xlsx"

# Duruş analizi fonksiyonları
def analyze_posture(landmarks):
    # Landmark koordinatları
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
    nose = landmarks[mp_pose.PoseLandmark.NOSE.value]

    # Omuz hiza
    shoulder_slope = abs(left_shoulder.y - right_shoulder.y)

    # Kamburluk kontrolü (boyun eğimi)
    neck_slope = abs(nose.x - ((left_shoulder.x + right_shoulder.x) / 2))

    # Duruş analizi eşikleri
    is_correct = shoulder_slope < 0.04 and neck_slope < 0.1
    return is_correct, shoulder_slope, neck_slope

# Grafik güncelleme fonksiyonu
def update_chart(shoulder_slope, neck_slope):
    plt.clf()
    plt.bar(["Omuz Hizası", "Boyun Hizası"], [shoulder_slope, neck_slope], color=['blue', 'orange'])
    plt.axhline(0.04, color='red', linestyle='--', label='Omuz Eşik Değeri')
    plt.axhline(0.04, color='green', linestyle='--', label='Boyun Eşik Değeri')
    plt.legend()
    canvas.draw()

# Veri kaydı fonksiyonu
def log_data(timestamp, is_correct):
    global data_records
    status = "Doğru" if is_correct else "Hatalı Duruş, Lütfen Düzeltin"
    data_records.append({"Timestamp": timestamp, "Posture": status})

# Excel dosya kaydet
def save_to_excel():
    global data_records
    df = pd.DataFrame(data_records)
    df.to_excel(data_file, index=False)

# Gerçek zamanlı duruş analizi
def start_camera():
    global speech_enabled, posture_last_correct, last_feedback_time

    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            is_correct, shoulder_slope, neck_slope = analyze_posture(landmarks)

            # Çizim
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            current_time = time.time()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            # Geribildirim
            if is_correct:
                cv2.putText(image, "Posture: Correct", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                if posture_last_correct is False or (current_time - last_feedback_time > feedback_interval):
                    if speech_enabled:
                        start_speech_thread("Your posture is correct. Keep it up!")
                    last_feedback_time = current_time
                posture_last_correct = True
            else:
                cv2.putText(image, "Durus: HATALI", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                if posture_last_correct is True or (current_time - last_feedback_time > feedback_interval):
                    if speech_enabled:
                        start_speech_thread("Lutfen durusunu duzeltiniz.")
                    last_feedback_time = current_time
                posture_last_correct = False

            # Veri kaydı
            log_data(timestamp, is_correct)

            # Grafik güncelleme
            update_chart(shoulder_slope, neck_slope)

        # OpenCV görüntüsünü GUI'de göster
        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img = ImageTk.PhotoImage(image=Image.fromarray(img))
        video_label.imgtk = img
        video_label.configure(image=img)
        root.update()

    cap.release()
    cv2.destroyAllWindows()
    save_to_excel()

root = tk.Tk()
root.title("Postur Hatirlatici")
root.geometry("1000x700")


title = Label(root, text="Duruş Düzeltici Uygulaması", font=("Helvetica", 24))
title.pack()

# Video show etiket
video_label = Label(root)
video_label.pack()

# Kamera buton
start_button = tk.Button(root, text="Start Camera", command=start_camera, font=("Helvetica", 16))
start_button.pack()

# Sesli yanıt kontrolü için checkbox
speech_var = tk.BooleanVar(value=speech_enabled)
speech_checkbox = tk.Checkbutton(root, text="Enable Speech Feedback", variable=speech_var, command=lambda: toggle_speech())
speech_checkbox.pack()

def toggle_speech():
    global speech_enabled
    speech_enabled = speech_var.get()

# matplotlib canvas for grafik
fig, ax = plt.subplots()
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack()

# Koştur
root.mainloop()
