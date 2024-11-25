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

# Multithreading için : Sonradan ekledik
def speak(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
# Multithreading için : Sonradan eklendik
def start_speech_thread(text):
    # Sesli yanıtı ayrı bir iş parçacığında çalıştıralım / aksi takdirde sesli yanıt verirken ekran donuyor
    threading.Thread(target = speak,args = (text,)).start()


# Sesli yanıt için kontrol mekanizmaları
posture_correct = False
posture_correct_last = False


# MediaPipe Pose setup
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils


# Postur Analiz Fonksiyonlari
def analyze_posture(landmarks):
    # Omuz ve kalca egim hesaplanmasi
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]

    # Omuzların yatay hizası
    shoulder_slope = abs(left_shoulder.y - right_shoulder.y)

    # Kalça hizası
    hip_slope = abs(left_hip.y - right_hip.y)

    # Duruş analizi (basit bir eşik)
    posture_correct = shoulder_slope < 0.04 and hip_slope < 0.04
    return posture_correct


# Gercek zamanli postur duzeltme
def start_camera():
    global posture_correct, posture_correct_last

    cap = cv2.VideoCapture(0)
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Goruntu isleme ops.
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            posture_correct = analyze_posture(landmarks)

            # Cizim
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Feedback mekanizmasi
            if posture_correct and not posture_correct_last:
                cv2.putText(image, "Posture: Correct", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                text = "You have nice posture. Stay like this."
                start_speech_thread(text)
                posture_correct_last = True
            # Feedback mekanizmasi
            if not posture_correct and posture_correct_last:
                cv2.putText(image, "Posture: Incorrect", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                text = "Fix your position please"
                start_speech_thread(text)
                posture_correct_last = False

        # OpenCV'den gelen görüntüyü GUI'de göster
        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        img = ImageTk.PhotoImage(image=Image.fromarray(img))
        video_label.imgtk = img
        video_label.configure(image=img)
        root.update()

    cap.release()
    cv2.destroyAllWindows()

# GUI kurulum
root = tk.Tk()
root.title("Posture Rectifier")
root.geometry("800x600")

# GUI elemanlar
title = Label(root, text="Posture Rectifier", font=("Helvetica", 24))
title.pack()

video_label = Label(root)
video_label.pack()

start_button = tk.Button(root, text="Start Camera", command=start_camera, font=("Helvetica", 16))
start_button.pack()

# Main loop
root.mainloop()