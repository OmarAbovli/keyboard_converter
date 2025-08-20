#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Typer GUI
- Put/paste a long text (Arabic supported).
- Each keypress types the next character from the text.
- Local mode: types into the app's output box when the app is focused.
- Global mode (optional): types into any active window using the 'keyboard' library.
  Note: Requires 'pip install keyboard' and on some systems admin permissions.
- Hotkeys: F8 Start/Pause, F9 Reset.
"""
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Try to import the optional 'keyboard' library for global typing mode.
try:
    import keyboard  # type: ignore
    HAS_KEYBOARD = True
except Exception:
    HAS_KEYBOARD = False
    keyboard = None  # type: ignore

class AutoTyperApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Auto Typer - أي مفتاح = الحرف التالي")
        self.root.geometry("900x600")
        self.root.minsize(820, 520)

        # State
        self.text_data = ""
        self.index = 0
        self.running = False
        self.loop_var = tk.BooleanVar(value=False)
        self.mode_var = tk.StringVar(value="local")  # 'local' or 'global'

        # Build UI
        self._build_ui()

        # Keyboard hook handle (for global mode)
        self._kb_hook = None

        # Hotkeys
        self.root.bind("<F8>", lambda e: self.toggle_start_pause())
        self.root.bind("<F9>", lambda e: self.reset())

        # Local key binding (only fires in local mode with focus inside the app)
        self.root.bind_all("<Key>", self._on_local_key, add="+")

        self._update_status()

    # ---------------- UI -----------------
    def _build_ui(self):
        # Top controls
        top = ttk.Frame(self.root, padding=10)
        top.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(top, text="📂 فتح ملف نصي", command=self.load_file).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(top, text="💾 حفظ النص", command=self.save_text).pack(side=tk.LEFT, padx=8)

        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=12)

        ttk.Checkbutton(top, text="🔁 إعادة من البداية بعد الانتهاء", variable=self.loop_var,
                        command=self._update_status).pack(side=tk.LEFT, padx=8)

        mode_frame = ttk.Frame(top)
        mode_frame.pack(side=tk.LEFT, padx=16)
        ttk.Label(mode_frame, text="الوضع:").pack(side=tk.LEFT)
        ttk.Radiobutton(mode_frame, text="محلي داخل التطبيق", value="local",
                        variable=self.mode_var, command=self._on_mode_change).pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(mode_frame, text="عام ↔ أي نافذة (يتطلب keyboard)", value="global",
                        variable=self.mode_var, command=self._on_mode_change).pack(side=tk.LEFT, padx=6)

        if not HAS_KEYBOARD:
            tip = "💡 لتفعيل الوضع العام: نفّذ\npip install keyboard"
            ttk.Label(top, text=tip, foreground="#555").pack(side=tk.LEFT, padx=10)

        # Middle panes
        mid = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        mid.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=8)

        # Source text
        src_frame = ttk.Labelframe(mid, text="النص المصدر (ضع النص هنا)")
        self.src_text = tk.Text(src_frame, wrap="word", font=("Segoe UI", 11))
        self.src_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        mid.add(src_frame, weight=3)

        # Output / Log
        out_frame = ttk.Labelframe(mid, text="الناتج (للوضع المحلي)")
        self.out_text = tk.Text(out_frame, wrap="word", font=("Segoe UI", 11), state=tk.NORMAL)
        self.out_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        mid.add(out_frame, weight=2)

        # Bottom controls
        bottom = ttk.Frame(self.root, padding=10)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)

        self.start_btn = ttk.Button(bottom, text="▶️ بدء (F8)", command=self.toggle_start_pause)
        self.start_btn.pack(side=tk.LEFT)

        ttk.Button(bottom, text="⏹️ إيقاف/إعادة الضبط (F9)", command=self.reset).pack(side=tk.LEFT, padx=8)

        ttk.Separator(bottom, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=12)

        self.progress = ttk.Progressbar(bottom, length=300, mode="determinate")
        self.progress.pack(side=tk.LEFT, padx=8)

        self.status_lbl = ttk.Label(bottom, text="جاهز")
        self.status_lbl.pack(side=tk.RIGHT)

    # ---------------- Logic -----------------
    def load_text_from_widget(self):
        self.text_data = self.src_text.get("1.0", tk.END)
        # Normalize line endings but keep as-is otherwise
        if self.text_data.endswith("\n"):
            self.text_data = self.text_data[:-1]

    def _next_char(self):
        if not self.text_data:
            return None
        if self.index >= len(self.text_data):
            if self.loop_var.get():
                self.index = 0
            else:
                return None
        ch = self.text_data[self.index]
        self.index += 1
        return ch

    def _type_next_char(self):
        ch = self._next_char()
        if ch is None:
            # End reached
            self.running = False
            self._unbind_global()
            self._update_status()
            return

        if self.mode_var.get() == "global" and HAS_KEYBOARD:
            try:
                keyboard.write(ch)
            except Exception as e:
                messagebox.showerror("خطأ", f"تعذر الكتابة في الوضع العام: {e}")
                self.running = False
                self._unbind_global()
        else:
            # Local mode: write to output widget
            self.out_text.insert(tk.END, ch)
            self.out_text.see(tk.END)

        self._update_status()

    def _on_local_key(self, event):
        # Only respond to actual keypresses in local mode and when running
        if not self.running or self.mode_var.get() != "local":
            return
        # Ignore modifier-only events (Shift, Control, etc.)
        if len(event.keysym) > 1 and event.keysym.lower() not in ("space", "return", "tab", "backspace", "delete"):
            # Still consume as a trigger, but no special handling needed
            pass
        self._type_next_char()

    def _global_key_worker(self):
        # Runs in background to listen to any key and type next char
        # We use keyboard.on_press to trigger on any key press
        if not HAS_KEYBOARD:
            return

        def _callback(event):
            if not self.running:
                return
            # Ignore auto-typing keys generated by ourselves? (keyboard library might produce events)
            # We skip if the event name is None
            try:
                self._type_next_char()
            except Exception:
                pass

        self._kb_hook = keyboard.on_press(_callback)
        # Wait until stopped
        while self.running:
            keyboard.wait("esc" if False else None)  # just idle
            if not self.running:
                break

    def _bind_global(self):
        if self._kb_hook is not None:
            return
        t = threading.Thread(target=self._global_key_worker, daemon=True)
        t.start()

    def _unbind_global(self):
        if HAS_KEYBOARD and self._kb_hook is not None:
            try:
                keyboard.unhook(self._kb_hook)
            except Exception:
                pass
            finally:
                self._kb_hook = None

    def toggle_start_pause(self):
        if not self.running:
            # Load text source fresh every start
            self.load_text_from_widget()
            if not self.text_data:
                messagebox.showwarning("تنبيه", "فضلاً أدخل نصاً في صندوق 'النص المصدر'.")
                return
            self.running = True
            if self.mode_var.get() == "global":
                if not HAS_KEYBOARD:
                    messagebox.showwarning(
                        "الوضع العام غير متاح",
                        "مكتبة 'keyboard' غير مثبتة.\nنفّذ:\n    pip install keyboard\nأو استخدم الوضع المحلي داخل التطبيق."
                    )
                    self.running = False
                    return
                self._bind_global()
            self.start_btn.config(text="⏸️ إيقاف مؤقت (F8)")
        else:
            # Pause
            self.running = False
            self._unbind_global()
            self.start_btn.config(text="▶️ متابعة (F8)")
        self._update_status()

    def reset(self):
        self.running = False
        self._unbind_global()
        self.index = 0
        self.start_btn.config(text="▶️ بدء (F8)")
        # Clear local output
        self.out_text.delete("1.0", tk.END)
        self._update_status()

    def _update_status(self):
        total = len(self.text_data)
        idx = min(self.index, total)
        pct = 0 if total == 0 else int((idx / total) * 100)
        self.progress["maximum"] = max(total, 1)
        self.progress["value"] = idx
        mode_label = "عام (Global)" if (self.mode_var.get() == "global") else "محلي (Local)"
        run_state = "يعمل" if self.running else "متوقف"
        self.status_lbl.config(text=f"الوضع: {mode_label} | الحالة: {run_state} | التقدم: {idx}/{total} ({pct}%)")

    def _on_mode_change(self):
        # If switching mode while running, stop and require restart
        if self.running:
            self.toggle_start_pause()
        self._update_status()

    # -------- File ops --------
    def load_file(self):
        path = filedialog.askopenfilename(
            title="اختر ملف نصي",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = f.read()
            self.src_text.delete("1.0", tk.END)
            self.src_text.insert("1.0", data)
            self.index = 0
            self._update_status()
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر فتح الملف:\n{e}")

    def save_text(self):
        path = filedialog.asksaveasfilename(
            title="حفظ النص",
            defaultextension=".txt",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*")),
        )
        if not path:
            return
        try:
            data = self.src_text.get("1.0", tk.END)
            with open(path, "w", encoding="utf-8") as f:
                f.write(data)
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر حفظ الملف:\n{e}")

def main():
    root = tk.Tk()
    # Use ttk theme if available
    try:
        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except Exception:
        pass
    app = AutoTyperApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
