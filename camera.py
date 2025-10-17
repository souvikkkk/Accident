import cv2
from detection import AccidentDetectionModel
import numpy as np
import os
import winsound
import threading
import time
import smtplib
from email.message import EmailMessage

# Global variables
alarm_triggered = False
latest_photo_path = None
last_alert_time = 0
cooldown_seconds = 5  # cooldown time between alerts

# Load model
model = AccidentDetectionModel("model.json", "model_weights.keras")
font = cv2.FONT_HERSHEY_SIMPLEX


def save_accident_photo(frame):
    try:
        current_date_time = time.strftime("%Y-%m-%d-%H%M%S")
        directory = "accident_photos"
        if not os.path.exists(directory):
            os.makedirs(directory)
        filename = f"{directory}/{current_date_time}.jpg"
        cv2.imwrite(filename, frame)
        print(f"📸 Accident photo saved as {filename}")
        return filename
    except Exception as e:
        print(f"Error saving accident photo: {e}")
        return None


def send_email_with_photo(photo_path):
    try:
        sender_email = "souvikmukherjee018@gmail.com"
        receiver_emails = ["souvikmukherjee084@gmail.com"]
        password = "saog dswk yygk emei"  # Gmail App Password

        msg = EmailMessage()
        msg["Subject"] = "🚨 Accident Detected!"
        msg["From"] = sender_email
        msg["To"] = ", ".join(receiver_emails)
        msg.set_content("An accident has been detected. See the attached photo.")

        with open(photo_path, "rb") as f:
            img_data = f.read()
            msg.add_attachment(img_data, maintype="image", subtype="jpeg",
                               filename=os.path.basename(photo_path))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)

        print("📧 Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")


def alert_actions():
    frequency = 2500
    duration = 2000
    winsound.Beep(frequency, duration)

    if latest_photo_path:
        send_email_with_photo(latest_photo_path)


def start_alert_thread():
    thread = threading.Thread(target=alert_actions)
    thread.daemon = True
    thread.start()


def process_frame(frame, pred, prob):
    global alarm_triggered, latest_photo_path, last_alert_time

    if pred == "Accident" and prob[0][0] > 0.99:
        current_time = time.time()
        if not alarm_triggered or (current_time - last_alert_time) >= cooldown_seconds:
            latest_photo_path = save_accident_photo(frame)
            alarm_triggered = True
            last_alert_time = current_time
            start_alert_thread()
    return f"{pred} {round(prob[0][0] * 100, 2)}%"


def startapplication():
    global alarm_triggered

    video1 = cv2.VideoCapture("test_video.mp4")
    video2 = cv2.VideoCapture("test_video_2.mp4")

    while True:
        ret1, frame1 = video1.read()
        ret2, frame2 = video2.read()

        if not ret1 and not ret2:
            break

        if ret1:
            gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB)
            roi1 = cv2.resize(gray1, (250, 250))
            pred1, prob1 = model.predict_accident(roi1[np.newaxis, :, :])
            text1 = process_frame(frame1, pred1, prob1)
            cv2.putText(frame1, text1, (10, 30), font, 1, (0, 255, 255), 2)
            cv2.imshow("🚗 Accident Detection - Camera 1", frame1)

        if ret2:
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2RGB)
            roi2 = cv2.resize(gray2, (250, 250))
            pred2, prob2 = model.predict_accident(roi2[np.newaxis, :, :])
            text2 = process_frame(frame2, pred2, prob2)
            cv2.putText(frame2, text2, (10, 30), font, 1, (0, 255, 255), 2)
            cv2.imshow("🚗 Accident Detection - Camera 2", frame2)

        if cv2.waitKey(33) & 0xFF == ord('q'):
            break

    video1.release()
    video2.release()
    cv2.destroyAllWindows()
