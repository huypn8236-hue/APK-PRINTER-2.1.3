[app]

# --- Thông tin ứng dụng ---
title = Order Printer
package.name = orderprinter
package.domain = org.orderprinter

# --- File nguồn ---
source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,xml,json

# --- Phiên bản ---
version = 1.0.0

# --- Hiển thị ---
orientation = portrait
fullscreen = 0

# --- Thư viện yêu cầu (ĐÃ SỬA) ---
requirements = python3,kivy==2.2.1,pyjnius,android,pillow==10.2.0,plyer,certifi,kivy-garden.zbarcam

# --- Quyền Android ---
android.permissions = CAMERA,INTERNET,ACCESS_NETWORK_STATE,BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_CONNECT,BLUETOOTH_SCAN,ACCESS_FINE_LOCATION,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE

# --- Tài nguyên đính kèm (có thể bỏ dòng này nếu không có file) ---
# android.add_assets = wifi_printers.json

# --- Màn hình khởi động ---
android.presplash_color = #FFFFFF

# --- Android SDK / NDK (ĐÃ SỬA) ---
android.api = 30
android.minapi = 21
android.ndk = 23b
android.ndk_api = 21
android.archs = arm64-v8a,armeabi-v7a

# --- p4a branch (ĐÃ SỬA) ---
p4a.branch = develop

android.allow_backup = True
android.accept_sdk_license = True
android.enable_androidx = True

# --- Giảm kích thước APK ---
exclude_patterns = tests,docs,*.pyc,*.pyo,*.md,__pycache__,.git

# --- Môi trường ---
environment = 
    PYTHONOPTIMIZE=2
    KIVY_METRICS_DENSITY=2

[buildozer]
log_level = 2
warn_on_root = 1
