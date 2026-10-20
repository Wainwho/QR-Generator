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
from PIL import Image, ImageDraw
from flask import Flask, render_template, request, jsonify
import qrcode
import qrcode.image.svg
from PyQt6.QtCore import Qt, QByteArray
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)

app = Flask(__name__)

TRANSLATIONS = {
    "ru": {
        "title": "Сервер запущен!",
        "subtitle": "Отсканируй для входа с телефона:",
        "copy_btn": "Скопировать ссылку",
        "web_title": "QR Генератор",
        "web_subtitle": "Создай кастомный QR-код (PNG / SVG)",
        "open_tab": "🔗 Открыть приложение в новой вкладке",
        "input_label": "Ссылка или текст",
        "input_placeholder": "https://example.com",
        "format_label": "Формат сохранения",
        "gradient_label": "Использовать градиент",
        "color1_label": "Цвет узоров",
        "color1_grad_label": "Начальный цвет",
        "color2_label": "Конечный цвет",
        "bg_label": "Цвет фона",
        "gen_btn": "Сгенерировать код",
        "download_btn": "Скачать файл",
    },
    "en": {
        "title": "Server is running!",
        "subtitle": "Scan to open on mobile:",
        "copy_btn": "Copy Link",
        "web_title": "QR Generator",
        "web_subtitle": "Create custom QR code (PNG / SVG)",
        "open_tab": "🔗 Open app in a new tab",
        "input_label": "URL or Text",
        "input_placeholder": "https://example.com",
        "format_label": "Save Format",
        "gradient_label": "Use Gradient",
        "color1_label": "Pattern Color",
        "color1_grad_label": "Start Color",
        "color2_label": "End Color",
        "bg_label": "Background Color",
        "gen_btn": "Generate Code",
        "download_btn": "Download File",
    },
}


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
  lang = request.args.get("lang", "ru")
  if lang not in TRANSLATIONS:
    lang = "ru"
  return render_template("index.html", t=TRANSLATIONS[lang], current_lang=lang)


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
  file_format = req_data.get("format", "png")

  if not data:
    return jsonify({"error": "Пустая ссылка или текст"}), 400

  # Для SVG делаем стандартный чистый векторный QR-код
  if file_format == "svg":
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
        image_factory=factory,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image()
    svg_io = BytesIO()
    img.save(svg_io)
    svg_str = svg_io.getvalue().decode("utf-8")

    svg_base64 = base64.b64encode(svg_str.encode("utf-8")).decode("utf-8")
    return jsonify(
        {
            "qr_image": f"data:image/svg+xml;base64,{svg_base64}",
            "format": "svg",
        }
    )

  # Генерация PNG с поддержкой цветов и градиентов
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

  return jsonify(
      {"qr_image": f"data:image/png;base64,{img_str}", "format": "png"}
  )


def run_flask():
  import logging

  log = logging.getLogger("werkzeug")
  log.setLevel(logging.ERROR)
  app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


class MainWindow(QMainWindow):

  def __init__(self, url):
    super().__init__()
    self.url = url
    self.lang = "ru"
    self.initUI()

  def initUI(self):
    self.setWindowTitle("QR Generator Server")
    self.setFixedSize(380, 520)
    self.setStyleSheet(
        """
            QMainWindow { background-color: #030712; }
            QLabel { color: #f8fafc; font-family: 'Plus Jakarta Sans', sans-serif; }
            QPushButton {
                background-color: #4f46e5;
                color: white;
                border-radius: 14px;
                font-weight: bold;
                font-size: 13px;
                font-family: 'Plus Jakarta Sans', sans-serif;
                border: none;
            }
            QPushButton:hover { background-color: #4338ca; }
            QPushButton:pressed { background-color: #3730a3; }
        """
    )

    central_widget = QWidget()
    self.setCentralWidget(central_widget)
    layout = QVBoxLayout(central_widget)
    layout.setContentsMargins(30, 20, 30, 30)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    lang_layout = QHBoxLayout()
    lang_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

    self.btn_ru = QPushButton("RU")
    self.btn_ru.setFixedSize(36, 36)
    self.btn_ru.setStyleSheet(
        "border-radius: 18px; background-color: #4f46e5; font-size: 11px;"
    )
    self.btn_ru.clicked.connect(lambda: self.change_lang("ru"))

    self.btn_en = QPushButton("EN")
    self.btn_en.setFixedSize(36, 36)
    self.btn_en.setStyleSheet(
        "border-radius: 18px; background-color: #1f2937; color: #94a3b8;"
        " font-size: 11px;"
    )
    self.btn_en.clicked.connect(lambda: self.change_lang("en"))

    lang_layout.addWidget(self.btn_ru)
    lang_layout.addWidget(self.btn_en)
    layout.addLayout(lang_layout)

    self.title = QLabel()
    self.title.setStyleSheet(
        "font-size: 20px; font-weight: bold; color: #38bdf8;"
    )
    self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(self.title)

    self.subtitle = QLabel()
    self.subtitle.setStyleSheet(
        "font-size: 12px; color: #94a3b8; margin-bottom: 5px;"
    )
    self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(self.subtitle)

    qr = qrcode.QRCode(box_size=5, border=1)
    qr.add_data(self.url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")

    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    qt_image = QPixmap()
    qt_image.loadFromData(QByteArray(buffer.getvalue()))

    self.qr_label = QLabel()
    self.qr_label.setPixmap(qt_image)
    self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.qr_label.setStyleSheet(
        "background-color: white; border-radius: 16px; padding: 10px;"
    )
    layout.addWidget(self.qr_label)

    self.url_label = QLabel(self.url)
    self.url_label.setStyleSheet(
        "font-size: 12px; color: #cbd5e1; background-color: #111827; border: 1px"
        " solid #1f2937; border-radius: 12px; padding: 10px;"
    )
    self.url_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.url_label.setWordWrap(True)
    layout.addWidget(self.url_label)

    self.copy_btn = QPushButton()
    self.copy_btn.setFixedHeight(45)
    self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    self.copy_btn.clicked.connect(self.copy_link)
    layout.addWidget(self.copy_btn)

    self.update_texts()

  def change_lang(self, lang):
    self.lang = lang
    if lang == "ru":
      self.btn_ru.setStyleSheet(
          "border-radius: 18px; background-color: #4f46e5; font-size: 11px;"
      )
      self.btn_en.setStyleSheet(
          "border-radius: 18px; background-color: #1f2937; color: #94a3b8;"
          " font-size: 11px;"
      )
    else:
      self.btn_en.setStyleSheet(
          "border-radius: 18px; background-color: #4f46e5; font-size: 11px;"
      )
      self.btn_ru.setStyleSheet(
          "border-radius: 18px; background-color: #1f2937; color: #94a3b8;"
          " font-size: 11px;"
      )
    self.update_texts()

  def update_texts(self):
    t = TRANSLATIONS[self.lang]
    self.title.setText(t["title"])
    self.subtitle.setText(t["subtitle"])
    self.copy_btn.setText(t["copy_btn"])

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
