[app]

# ==================================================
# APP INFO
# ==================================================
title = Order Printer
package.name = orderprinter
package.domain = org.example

version = 1.0.0

# ==================================================
# SOURCE
# ==================================================
source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,json,kv

# loại file không cần đóng gói
exclude_patterns = \
    tests,\
    docs,\
    *.pyc,\
    *.pyo,\
    *.md,\
    __pycache__,\
    .git,\
    .github

# ==================================================
# ICON / SPLASH
# ==================================================
icon.filename = %(source.dir)s/icon.png

presplash.filename = %(source.dir)s/icon.png
android.presplash_color = #FFFFFF

# ==================================================
# DISPLAY
# ==================================================
orientation = portrait
fullscreen = 0

# ==================================================
# REQUIREMENTS
# ==================================================
# KHỚP trực tiếp với code main.py:
#
# - kivy
# - pyjnius
# - pillow
# - certifi
# - plyer
# - zbarcam
#
# KHÔNG thêm reportlab vì Android không dùng
#
requirements = \
    python3==3.10.11,\
    kivy==2.3.0,\
    pyjnius,\
    pillow,\
    plyer,\
    certifi,\
    kivy-garden.zbarcam

# ==================================================
# ANDROID PERMISSIONS
# ==================================================
# CAMERA -> scan barcode
# INTERNET -> Wi-Fi print
# ACCESS_NETWORK_STATE -> kiểm tra mạng
# Bluetooth -> ESC/POS printer
#
android.permissions = \
    CAMERA,\
    INTERNET,\
    ACCESS_NETWORK_STATE,\
    BLUETOOTH,\
    BLUETOOTH_ADMIN,\
    BLUETOOTH_CONNECT,\
    BLUETOOTH_SCAN,\
    ACCESS_FINE_LOCATION,\
    VIBRATE

# NOTE:
# WRITE_EXTERNAL_STORAGE & READ_EXTERNAL_STORAGE
# đã deprecated Android 13+
# app hiện không cần storage ngoài

# ==================================================
# ASSETS
# ==================================================
android.add_assets = wifi_printers.json

# NOTE:
# arial.ttf chưa được code sử dụng
# không cần add vào APK

# ==================================================
# ANDROID SDK / NDK
# ==================================================
android.api = 34

# Bluetooth modern APIs ổn định hơn từ 24+
android.minapi = 24

android.ndk = 25b
android.ndk_api = 24

android.archs = arm64-v8a,armeabi-v7a

android.accept_sdk_license = True
android.enable_androidx = True
android.allow_backup = True

# ==================================================
# PYTHON-FOR-ANDROID
# ==================================================
# develop hiện ổn định hơn master
# đặc biệt trên GitHub Actions
#
p4a.branch = develop

# rất quan trọng cho camera + kivy
p4a.bootstrap = sdl2

# ==================================================
# ENVIRONMENT
# ==================================================
environment = \
    PYTHONOPTIMIZE=2,\
    KIVY_METRICS_DENSITY=2

# ==================================================
# BUILD
# ==================================================
[buildozer]

log_level = 2
warn_on_root = 0
