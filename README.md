# Python & Flask QR Code Generator

A lightweight, modern web and desktop application for generating and customizing QR codes on the fly. Designed for seamless usage across both PC and mobile devices over a local network.

---

## 🚀 Features

- **Desktop GUI (Tkinter):** Automatically starts a local server and displays a native window containing the local IP address, a scan-ready QR code, and a one-click button to copy the app link.
- **Mobile & PC Friendly:** Access the web interface instantly from your smartphone by scanning the desktop QR code or from your PC using the quick-link button.
- **Custom QR Styling:** Choose custom foreground (dot) and background colors for your QR codes.
- **Instant PNG Export:** Generate and download high-resolution QR codes directly to your device.
- **Auto-Dependency Installation:** The application automatically checks for required libraries (`Flask`, `qrcode`, `Pillow`) on startup and installs them if missing.

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask, Qrcode, Pillow
- **GUI:** Tkinter
- **Frontend:** HTML5, Tailwind CSS, JavaScript

---

## 📦 Installation & Setup

1. **Clone or download** this repository to your computer.
2. Ensure you have the `templates` folder in your project directory containing `index.html`.
3. Run the application using Python:
   ```bash
   python app.py
   ```
4. The application will automatically check dependencies, start the background web server, and pop up the desktop window with the local network QR code!
