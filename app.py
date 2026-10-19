import subprocess
import sys

required_packages = ["flask", "qrcode[pil]", "Pillow"]

for package in required_packages:
  try:
    if "qrcode" in package:
      import qrcode
    elif "flask" in package:
      import flask
    elif "Pillow" in package:
      from PIL import Image
  except ImportError:
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", package],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

from io import BytesIO
import base64
import socket
import threading
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from flask import Flask, render_template, request, jsonify
import qrcode

app = Flask(__name__)


def get_local_ip():
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip
  except Exception:
    return "127.0.0.1"


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate_qr():
  req_data = request.json
  data = req_data.get("text", "").strip()
  fill_color = req_data.get("fill_color", "#000000")
  back_color = req_data.get("back_color", "#ffffff")

  if not data:
    return jsonify({"error": "Пустая ссылка или текст"}), 400

  qr = qrcode.QRCode(
      version=None,
      error_correction=qrcode.constants.ERROR_CORRECT_M,
      box_size=10,
      border=2,
  )
  qr.add_data(data)
  qr.make(fit=True)

  img = qr.make_image(fill_color=fill_color, back_color=back_color)

  buffered = BytesIO()
  img.save(buffered, format="PNG")
  img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

  return jsonify({"qr_image": f"data:image/png;base64,{img_str}"})


def run_flask():
  import logging

  log = logging.getLogger("werkzeug")
  log.setLevel(logging.ERROR)
  app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


def start_gui(url):
  root = tk.Tk()
  root.title("QR Generator Server")
  root.geometry("360x450")
  root.configure(bg="#090d16")
  root.resizable(False, False)

  title_label = tk.Label(
      root,
      text="Сервер запущен!",
      font=("Helvetica", 16, "bold"),
      fg="#38bdf8",
      bg="#090d16",
  )
  title_label.pack(pady=(20, 5))

  subtitle_label = tk.Label(
      root,
      text="Отсканируй для входа с телефона:",
      font=("Helvetica", 10),
      fg="#94a3b8",
      bg="#090d16",
  )
  subtitle_label.pack(pady=(0, 15))

  qr = qrcode.QRCode(box_size=6, border=1)
  qr.add_data(url)
  qr.make(fit=True)
  qr_img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")

  img_tk = ImageTk.PhotoImage(qr_img)

  qr_label = tk.Label(root, image=img_tk, bg="#090d16")
  qr_label.image = img_tk
  qr_label.pack(pady=5)

  url_label = tk.Label(
      root,
      text=url,
      font=("Helvetica", 11),
      fg="#e2e8f0",
      bg="#090d16",
      wraplength=320,
  )
  url_label.pack(pady=15)

  def copy_link():
    root.clipboard_clear()
    root.clipboard_append(url)
    messagebox.showinfo("Успех", "Ссылка скопирована в буфер обмена!")

  copy_btn = tk.Button(
      root,
      text="Скопировать ссылку",
      command=copy_link,
      font=("Helvetica", 10, "bold"),
      bg="#4f46e5",
      fg="#ffffff",
      activebackground="#4338ca",
      activeforeground="#ffffff",
      relief="flat",
      padx=15,
      pady=8,
      cursor="hand2",
  )
  copy_btn.pack(pady=5)

  root.mainloop()


if __name__ == "__main__":
  IP = get_local_ip()
  PORT = 5000
  url = f"http://{IP}:{PORT}"

  flask_thread = threading.Thread(target=run_flask, daemon=True)
  flask_thread.start()

  start_gui(url)
