import sys
import webbrowser
import speech_recognition as sr
import sounddevice as sd
import scipy.io.wavfile as wav
import io
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget, QLabel


class VoiceRecognizerThread(QThread):
    text_recognized = pyqtSignal(str)
    status_changed = pyqtSignal(str)

    def run(self):
        self.status_changed.emit("Слушаю вас... Говорите (5 сек).")
        try:
            # Запись звука без PyAudio (частота 16000 Гц, длительность 5 секунд)
            fs = 16000
            duration = 5
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()  # Ожидание окончания записи

            self.status_changed.emit("Распознаю речь...")

            # Сохраняем в буфер памяти как WAV файл
            wav_io = io.BytesIO()
            wav.write(wav_io, fs, recording)
            wav_io.seek(0)

            # Передаем в SpeechRecognition
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_io) as source:
                audio = recognizer.record(source)

            text = recognizer.recognize_google(audio, language="ru-RU")
            self.text_recognized.emit(text)

        except sr.UnknownValueError:
            self.status_changed.emit("Не удалось распознать речь.")
        except sr.RequestError:
            self.status_changed.emit("Ошибка сервиса распознавания.")
        except Exception as e:
            self.status_changed.emit(f"Ошибка: {str(e)}")


class VoiceAssistantApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Голосовой помощник (Без PyAudio)")
        self.resize(400, 300)
        self.status_label = QLabel("Нажмите кнопку, чтобы дать команду", self)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.log_box = QTextEdit(self)
        self.log_box.setReadOnly(True)
        self.listen_btn = QPushButton("Включить микрофон", self)
        self.listen_btn.clicked.connect(self.start_listening)

        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.log_box)
        layout.addWidget(self.listen_btn)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def start_listening(self):
        self.listen_btn.setEnabled(False)
        self.thread = VoiceRecognizerThread()
        self.thread.text_recognized.connect(self.handle_command)
        self.thread.status_changed.connect(self.update_status)
        self.thread.finished.connect(lambda: self.listen_btn.setEnabled(True))
        self.thread.start()

    def update_status(self, status_text):
        self.status_label.setText(status_text)

    def handle_command(self, text):
        command = text.lower()
        self.log_box.append(f"Вы сказали: {text}")

        if "ютуб" in command or "youtube" in command:
            webbrowser.open("https://youtube.com")
            self.status_label.setText("Команда выполнена!")
        elif "вк" in command or "вконтакте" in command:
            webbrowser.open("https://vk.com")
            self.status_label.setText("Команда выполнена!")
        else:
            self.log_box.append("Система: Команда не распознана.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VoiceAssistantApp()
    window.show()
    sys.exit(app.exec())
