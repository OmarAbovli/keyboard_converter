# -*- coding: utf-8 -*-
import sys
import time
import keyboard
import win32gui, win32con, win32api
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QPalette, QColor


# ============== Worker ==============
class TypingWorker(QThread):
    progress = pyqtSignal(int, int) 
    state = pyqtSignal(str)

    def __init__(self, text, loop=False):
        super().__init__()
        self.text = text
        self.loop = loop
        self.idx = 0
        self.running = False
        self.paused = False
        self.key_pressed = False  # هل فيه زرار مضغوط؟

    def run(self):
        self.running = True
        self.paused = False
        self.state.emit("Running...")
        self.progress.emit(self.idx, len(self.text))

        keyboard.add_hotkey("shift", self._toggle_pause)
        keyboard.on_press(self._on_key_down)
        keyboard.on_release(self._on_key_up)

        while self.running:
            if self.paused or not self.key_pressed:
                time.sleep(0.01)
                continue

            if self.idx >= len(self.text):
                if self.loop:
                    self.idx = 0
                else:
                    self.stop()
                    return

            ch = self.text[self.idx]
            self.idx += 1
            self.progress.emit(self.idx, len(self.text))
            self._send_char(ch)

            time.sleep(0.05)  # ⏱️ سرعة الكتابة (تقدر تزود/تنقص)

        keyboard.unhook_all()
        self.state.emit("Stopped")

    def _on_key_down(self, e):
        if self.running and not self.paused and e.name not in ("shift", "shiftleft", "shiftright"):
            self.key_pressed = True

    def _on_key_up(self, e):
        if self.running and e.name not in ("shift", "shiftleft", "shiftright"):
            self.key_pressed = False

    def _toggle_pause(self):
        if not self.running:
            return
        self.paused = not self.paused
        self.state.emit("Paused" if self.paused else "Running...")

    def _send_char(self, ch):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if ch == "\n":
                win32api.SendMessage(hwnd, win32con.WM_CHAR, 0x0D, 0)
            else:
                for code in ch.encode("utf-16le"):
                    win32api.SendMessage(hwnd, win32con.WM_CHAR, code, 0)
        except Exception:
            pass

    def stop(self):
        self.running = False
        self.paused = False
        self.key_pressed = False


# ============== UI ==============
class TypingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.worker = None
        self._build_ui()

    def _build_ui(self):
        self.setWindowTitle("✦ Typing Simulator ✦")
        self.resize(820, 560)

        pal = QPalette()
        pal.setColor(QPalette.Window, QColor("#0f172a"))
        pal.setColor(QPalette.WindowText, Qt.white)
        self.setPalette(pal)

        root = QVBoxLayout(self)
        title = QLabel("زر Run ثم اكتب بأي زر مطول — سيُكتب النص حرفًا حرفًا.\nShift: إيقاف/استئناف • Stop: إيقاف كامل")
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 11))
        title.setStyleSheet("color:#9ca3af;")
        root.addWidget(title)

        self.text = QTextEdit()
        self.text.setFont(QFont("Consolas", 13))
        self.text.setStyleSheet("background:#0b1220; color:#e5e7eb; border:1px solid #1f2937; border-radius:10px; padding:12px;")
        root.addWidget(self.text, 1)

        controls = QHBoxLayout()
        root.addLayout(controls)

        self.run_btn = QPushButton("▶ Run")
        self.run_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.run_btn.setStyleSheet("background:#10b981; color:white; padding:10px 18px; border:none; border-radius:10px;")
        self.run_btn.clicked.connect(self.start_run)
        controls.addWidget(self.run_btn)

        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.stop_btn.setStyleSheet("background:#ef4444; color:white; padding:10px 18px; border:none; border-radius:10px;")
        self.stop_btn.clicked.connect(self.stop_run)
        controls.addWidget(self.stop_btn)

        self.loop_btn = QPushButton("↻ Loop: OFF")
        self.loop_btn.setCheckable(True)
        self.loop_btn.setFont(QFont("Segoe UI", 12))
        self.loop_btn.setStyleSheet("""
            QPushButton { background:#334155; color:#e5e7eb; padding:10px 18px; border:none; border-radius:10px; }
            QPushButton:checked { background:#3b82f6; color:white; }
        """)
        self.loop_btn.toggled.connect(lambda on: self.loop_btn.setText("↻ Loop: ON" if on else "↻ Loop: OFF"))
        controls.addWidget(self.loop_btn)

        status_row = QHBoxLayout()
        root.addLayout(status_row)

        self.status = QLabel("الحالة: Ready")
        self.status.setStyleSheet("color:#9ca3af;")
        self.status.setFont(QFont("Segoe UI", 11))
        status_row.addWidget(self.status)

        self.progress = QLabel("0 / 0")
        self.progress.setStyleSheet("color:#9ca3af;")
        self.progress.setFont(QFont("Segoe UI", 11))
        self.progress.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        status_row.addWidget(self.progress, 1)

    def start_run(self):
        text = self.text.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "تنبيه", "من فضلك أدخل نص أولاً.")
            return
        self.stop_run()
        self.worker = TypingWorker(text, loop=self.loop_btn.isChecked())
        self.worker.progress.connect(self._on_progress)
        self.worker.state.connect(self._on_state)
        self.worker.start()

    def stop_run(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(300)
        self.worker = None
        self.status.setText("الحالة: Stopped")
        self.progress.setText("0 / 0")

    def _on_progress(self, cur, total):
        self.progress.setText(f"{cur} / {total}")

    def _on_state(self, text):
        self.status.setText(f"الحالة: {text}")

    def closeEvent(self, e):
        self.stop_run()
        super().closeEvent(e)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = TypingApp()
    w.show()
    sys.exit(app.exec_())
