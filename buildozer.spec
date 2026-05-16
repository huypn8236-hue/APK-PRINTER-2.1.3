[app]
title = Order Printer
package.name = orderprinter
package.domain = org.orderprinter
source.dir = .
version = 1.0.0
orientation = portrait
fullscreen = 0

requirements = python3==3.10.12,kivy==2.2.1,pyjnius,android,pillow==10.2.0,plyer,certifi,kivy-garden.zbarcam

android.permissions = CAMERA,INTERNET,BLUETOOTH,BLUETOOTH_CONNECT,BLUETOOTH_SCAN,ACCESS_FINE_LOCATION
android.api = 30
android.minapi = 21
android.ndk = 23b
p4a.branch = develop
android.accept_sdk_license = True

[buildozer]
log_level = 2
