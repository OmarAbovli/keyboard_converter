import sys
import time
import threading
import pyautogui
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QTextEdit, QLabel, QMessageBox
)
from PyQt5.QtGui import QFont, QPalette, QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QShortcut
from PyQt5.QtGui import QKeySequence
import pyperclip


class AutoWriter(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.running = False

    def init_ui(self):
        self.setWindowTitle("✨ برنامج الكتابة التلقائية ✨")
        self.setGeometry(400, 200, 600, 400)

        # شكل مودرن للواجهة
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#1e1e2e"))
        palette.setColor(QPalette.WindowText, Qt.white)
        self.setPalette(palette)

        layout = QVBoxLayout()

        # عنوان
        title = QLabel("🖋️ اكتب النص أو الصقه واضغط Start")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # مربع النصوص
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Consolas", 14))
        self.text_edit.setStyleSheet("background-color: #2e2e3e; color: white; border-radius: 8px; padding: 10px;")
        layout.addWidget(self.text_edit)

        # زرار اللصق
        paste_btn = QPushButton("📋 Paste من الكليب بورد")
        paste_btn.setFont(QFont("Arial", 12))
        paste_btn.setStyleSheet("background-color: #3e8ef7; color: white; border-radius: 8px; padding: 10px;")
        paste_btn.clicked.connect(self.paste_text)
        layout.addWidget(paste_btn)

        # زرار Start
        self.start_btn = QPushButton("▶️ Start الكتابة")
        self.start_btn.setFont(QFont("Arial", 12))
        self.start_btn.setStyleSheet("background-color: #28a745; color: white; border-radius: 8px; padding: 10px;")
        self.start_btn.clicked.connect(self.start_writing)
        layout.addWidget(self.start_btn)

        # زرار Stop
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setFont(QFont("Arial", 12))
        self.stop_btn.setStyleSheet("background-color: #dc3545; color: white; border-radius: 8px; padding: 10px;")
        self.stop_btn.clicked.connect(self.stop_writing)
        layout.addWidget(self.stop_btn)

        # تعليمات
        info = QLabel("💡 ملاحظة: بعد الضغط على Start انتقل للبرنامج الآخر وسيبدأ بالكتابة تلقائياً.\n⏱️ السرعة محسوبة بدقة عالية.")
        info.setAlignment(Qt.AlignCenter)
        info.setFont(QFont("Arial", 10))
        layout.addWidget(info)

        # إضافة اختصار Ctrl+V للبيست
        shortcut = QShortcut(QKeySequence("Ctrl+V"), self)
        shortcut.activated.connect(self.paste_text)

        self.setLayout(layout)

    def paste_text(self):
        """لصق النص من الكليب بورد"""
        try:
            text = pyperclip.paste()
            self.text_edit.setPlainText(text)
        except Exception:
            QMessageBox.warning(self, "خطأ", "تعذر جلب النص من الكليب بورد!")

    def start_writing(self):
        """تشغيل الكتابة التلقائية"""
        if self.running:
            return

        text = self.text_edit.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "⚠️ تنبيه", "من فضلك اكتب أو الصق النص أولاً")
            return

        self.running = True
        t = threading.Thread(target=self.write_text, args=(text,))
        t.start()

    def write_text(self, text):
        time.sleep(2)  # وقت قصير عشان المستخدم يروح على المكان اللي عايز يكتب فيه
        for char in text:
            if not self.running:
                break
            pyautogui.typewrite(char)
            time.sleep(0.02)  # سرعة الكتابة (ممكن تزود أو تقلل)

    def stop_writing(self):
        """إيقاف الكتابة"""
        self.running = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoWriter()
    window.show()
    sys.exit(app.exec_())
