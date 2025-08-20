import tkinter as tk
from tkinter import messagebox
import pyperclip
import ttkbootstrap as tb

# خريطة التحويل من انجليزي لعربي (كيبورد)
eng_to_ar = {
    "q": "ض", "w": "ص", "e": "ث", "r": "ق", "t": "ف",
    "y": "غ", "u": "ع", "i": "ه", "o": "خ", "p": "ح",
    "[": "ج", "]": "د", "a": "ش", "s": "س", "d": "ي",
    "f": "ب", "g": "ل", "h": "ا", "j": "ت", "k": "ن",
    "l": "م", ";": "ك", "'": "ط", "z": "ئ", "x": "ء",
    "c": "ؤ", "v": "ر", "b": "لا", "n": "ى", "m": "ة",
    ",": "و", ".": "ز", "/": "ظ", "`": "ذ"
}

# العكس: من عربي لإنجليزي
ar_to_eng = {v: k for k, v in eng_to_ar.items()}

def detect_and_convert(text):
    # لو فيه حروف إنجليزية → حوّل لعربي
    if any("a" <= ch.lower() <= "z" or ch in eng_to_ar for ch in text):
        return "".join(eng_to_ar.get(ch.lower(), ch) for ch in text)
    # لو فيه حروف عربية → حوّل لإنجليزي
    elif any("\u0600" <= ch <= "\u06FF" for ch in text):
        return "".join(ar_to_eng.get(ch, ch) for ch in text)
    # لو نص مش مفهوم (أرقام/رموز فقط) → يرجعه زي ما هو
    return text

def on_convert():
    input_text = entry.get("1.0", tk.END).strip()
    if not input_text:
        messagebox.showwarning("⚠️ تنبيه", "من فضلك اكتب النص الأول")
        return
    result = detect_and_convert(input_text)
    output.delete("1.0", tk.END)
    output.insert(tk.END, result)

def copy_output():
    result = output.get("1.0", tk.END).strip()
    if result:
        pyperclip.copy(result)
        messagebox.showinfo("✅ نسخ", "تم نسخ النص الناتج!")
    else:
        messagebox.showwarning("⚠️ تنبيه", "مفيش نص تنسخه!")

# تصميم الواجهة
app = tb.Window(themename="superhero")
app.title("🔤 English ⇄ Arabic Keyboard Mapper")
app.geometry("700x500")

title = tb.Label(app, text="🔠 محول لوحة المفاتيح (عربي ⇄ إنجليزي)", 
                 font=("Cairo", 18, "bold"))
title.pack(pady=15)

# إدخال النص
frame1 = tb.LabelFrame(app, text=" ✍️ النص ", bootstyle="info")
frame1.pack(fill="both", padx=20, pady=10, expand=True)

entry = tk.Text(frame1, height=6, font=("Cairo", 14))
entry.pack(fill="both", padx=10, pady=10)

# زر التحويل
convert_btn = tb.Button(app, text="⚡ تحويل النص", 
                        bootstyle="success-outline", 
                        command=on_convert)
convert_btn.pack(pady=10)

# عرض الناتج
frame2 = tb.LabelFrame(app, text=" 📝 النص الناتج ", bootstyle="success")
frame2.pack(fill="both", padx=20, pady=10, expand=True)

output = tk.Text(frame2, height=6, font=("Cairo", 14))
output.pack(fill="both", padx=10, pady=10)

# زر نسخ
copy_btn = tb.Button(app, text="📋 نسخ الناتج", 
                     bootstyle="primary-outline", 
                     command=copy_output)
copy_btn.pack(pady=10)

app.mainloop()
