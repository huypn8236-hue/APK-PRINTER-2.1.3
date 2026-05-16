# buildozer.spec

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

exclude_patterns = 
tests,
docs,
*.pyc,
*.pyo,
*.md,
**pycache**,
.git,
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

requirements = 
python3==3.10.11,
kivy==2.3.0,
pyjnius,
pillow,
plyer,
certifi,
kivy-garden.zbarcam

# ==================================================

# ANDROID PERMISSIONS

# ==================================================

android.permissions = 
CAMERA,
INTERNET,
ACCESS_NETWORK_STATE,
BLUETOOTH,
BLUETOOTH_ADMIN,
BLUETOOTH_CONNECT,
BLUETOOTH_SCAN,
ACCESS_FINE_LOCATION,
VIBRATE

# ==================================================

# ASSETS

# ==================================================

android.add_assets = wifi_printers.json

# ==================================================

# ANDROID SDK / NDK

# ==================================================

android.api = 34
android.minapi = 24

android.ndk = 25b
android.ndk_api = 24

android.archs = arm64-v8a,armeabi-v7a

android.accept_sdk_license = True
android.enable_androidx = True
android.allow_backup = True

# ==================================================

# P4A

# ==================================================

p4a.bootstrap = sdl2

# ==================================================

# ENVIRONMENT

# ==================================================

environment = 
PYTHONOPTIMIZE=2,
KIVY_METRICS_DENSITY=2

# ==================================================

# BUILD

# ==================================================

[buildozer]

log_level = 2
warn_on_root = 0
