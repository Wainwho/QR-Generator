import subprocess
import sys

required_packages = ["flask", "qrcode[pil]", "Pillow", "PyQt6"]

for package in required_packages:
  try:
    if "qrcode" in package:
      import qrcode
    elif "flask" in package:
      import flask
    elif "Pillow" in package:
      from PIL import Image
    elif "PyQt6" in package:
      import PyQt6
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
from PIL import Image, ImageDraw, ImageOps
from flask import Flask, render_template, request, jsonify
import qrcode
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect,
)

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


def hex_to_rgb(hex_str):
  hex_str = hex_str.lstrip("#")
  return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))


@app.route("/generate", methods=["POST"])
def generate_qr():
  req_data = request.json
  data = req_data.get("text", "").strip()
  use_gradient = req_data.get("use_gradient", False)
  fill_color = req_data.get("fill_color", "#000000")
  fill_color_end = req_data.get("fill_color_end", "#4f46e5")
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

  img = qr.make_image(fill_color="#000000", back_color=back_color).convert(
      "RGBA"
  )
  width, height = img.size

  if use_gradient:
    color1 = hex_to_rgb(fill_color)
    color2 = hex_to_rgb(fill_color_end)

    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)
    for x in range(width):
      r = int(color1[0] + (color2[0] - color1[0]) * (x / width))
      g = int(color1[1] + (color2[1] - color1[1]) * (x / width))
      b = int(color1[2] + (color2[2] - color1[2]) * (x / width))
      draw.line([(x, 0), (x, height)], fill=(r, g, b, 255))

    pixels = img.load()
    grad_pixels = gradient.load()
    for y in range(height):
      for x in range(width):
        r, g, b, a = pixels[x, y]
        if r < 128:
          pixels[x, y] = grad_pixels[x, y]

    final_img = img.convert("RGB")
  else:
    fill_rgb = hex_to_rgb(fill_color)
    back_rgb = hex_to_rgb(back_color)
    img = qr.make_image(fill_color=fill_rgb, back_color=back_rgb)
    final_img = img.convert("RGB")

  buffered = BytesIO()
  final_img.save(buffered, format="PNG")
  img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

  return jsonify({"qr_image": f"data:image/png;base64,{img_str}"})


def run_flask():
  import logging

  log = logging.getLogger("werkzeug")
  log.setLevel(logging.ERROR)
  app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


class MainWindow(QMainWindow):

  def __init__(self, url):
    super().__init__()
    self.url = url
    self.initUI()

  def initUI(self):
    self.setWindowTitle("QR Generator Server")
    self.setFixedSize(380, 500)
    self.setStyleSheet(
        """
            QMainWindow {
                background-color: #030712;
            }
            QLabel {
                color: #f8fafc;
                font-family: 'Plus Jakarta Sans', sans-serif;
            }
            QPushButton {
                background-color: #4f46e5;
                color: white;
                border-radius: 14px;
                font-weight: bold;
                font-size: 13px;
                font-family: 'Plus Jakarta Sans', sans-serif;
                border: none;
            }
            QPushButton:hover {
                background-color: #4338ca;
            }
            QPushButton:pressed {
                background-color: #3730a3;
            }
        """
    )

    central_widget = QWidget()
    self.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    layout.setContentsMargins(30, 30, 30, 30)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    title = QLabel("Сервер запущен!")
    title.setStyleSheet(
        "font-size: 20px; font-weight: bold; color: #38bdf8;"
    )
    title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(title)

    subtitle = QLabel("Отсканируй для входа с телефона:")
    subtitle.setStyleSheet("font-size: 12px; color: #94a3b8; margin-bottom: 10px;")
    subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(subtitle)

    qr = qrcode.QRCode(box_size=5, border=1)
    qr.add_data(self.url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")

    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    qt_image = QPixmap()
    qt_image.loadFromData(QByteArray(buffer.getvalue()))

    qr_label = QLabel()
    qr_label.setPixmap(qt_image)
    qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    qr_label.setStyleSheet(
        "background-color: white; border-radius: 16px; padding: 12px;"
    )
    layout.addWidget(qr_label)

    url_label = QLabel(self.url)
    url_label.setStyleSheet(
        "font-size: 12px; color: #cbd5e1; background-color: #111827; border: 1px"
        " solid #1f2937; border-radius: 12px; padding: 10px;"
    )
    url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    url_label.setWordWrap(True)
    layout.addWidget(url_label)

    copy_btn = QPushButton("Скопировать ссылку")
    copy_btn.setFixedHeight(45)
    copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    copy_btn.clicked.connect(self.copy_link)
    layout.addWidget(copy_btn)

  def copy_link(self):
    clipboard = QApplication.clipboard()
    clipboard.setText(self.url)


if __name__ == "__main__":
  IP = get_local_ip()
  PORT = 5000
  url = f"http://{IP}:{PORT}"

  flask_thread = threading.Thread(target=run_flask, daemon=True)
  flask_thread.start()

  qt_app = QApplication(sys.argv)
  window = MainWindow(url)
  window.show()
  sys.exit(qt_app.exec())
