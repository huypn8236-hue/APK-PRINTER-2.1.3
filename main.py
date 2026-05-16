import os
import json
import time
import traceback
from datetime import datetime

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.metrics import dp, sp
from kivy.core.window import Window
from kivy.utils import platform
from kivy.graphics import Color, Rectangle, Line

# Chỉ import ZBarCam trên Android (tránh lỗi trên PC)
if platform == "android":
    from kivy_garden.zbarcam import ZBarCam

# ---------- CONFIG ----------
HISTORY_FILE = "print_history.json"
WIFI_PRINTERS_FILE = "wifi_printers.json"

# Màu sắc
COLOR_PRIMARY = (0.2, 0.55, 0.8, 1)
COLOR_SUCCESS = (0.2, 0.7, 0.3, 1)
COLOR_WARNING = (1, 0.5, 0, 1)
COLOR_ERROR = (0.8, 0.2, 0.2, 1)
COLOR_GRAY = (0.5, 0.5, 0.5, 1)
COLOR_BACKGROUND = (0.95, 0.95, 0.95, 1)
COLOR_WHITE = (1, 1, 1, 1)
COLOR_BLACK = (0, 0, 0, 1)


# ---------- HISTORY UTIL ----------
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


def save_history(h):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(h, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Warning: cannot save history:", e)


def add_history_entry(order_id, customer, box_qty):
    h = load_history()
    h.append({
        "order_id": str(order_id),
        "customer": str(customer),
        "box_qty": int(box_qty),
        "timestamp": datetime.now().isoformat()
    })
    save_history(h)


def has_been_printed(order_id):
    h = load_history()
    return any(item.get("order_id") == str(order_id) for item in h)


# ---------- WIFI PRINTERS ----------
def load_wifi_printers():
    if os.path.exists(WIFI_PRINTERS_FILE):
        try:
            with open(WIFI_PRINTERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


def save_wifi_printers(printers):
    try:
        with open(WIFI_PRINTERS_FILE, "w", encoding="utf-8") as f:
            json.dump(printers, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Warning: cannot save Wi-Fi printers:", e)


def add_wifi_printer(name, ip, port):
    printers = load_wifi_printers()
    for p in printers:
        if p["ip"] == ip and p["port"] == port:
            return
    printers.append({"name": name, "ip": ip, "port": port})
    save_wifi_printers(printers)


# ---------- PLATFORM CHECK ----------
def is_android():
    return platform == "android"


# ---------- IMPORT MODULES BASED ON PLATFORM ----------
if not is_android():
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm

    def create_pdf_a6_landscape(order_id, customer, box_qty):
        pagesize = (105*mm, 148*mm)
        filename = f"ORDER_{order_id}.pdf"
        try:
            c = canvas.Canvas(filename, pagesize=pagesize)
            width, height = pagesize
            margin = 10*mm
            
            for i in range(int(box_qty)):
                c.setFont("Helvetica-Bold", 28)
                c.drawString(margin, height - margin - 20, str(order_id)[:30])
                c.setFont("Helvetica", 18)
                c.drawString(margin, height - margin - 60, str(customer)[:30])
                c.setFont("Helvetica", 10)
                c.drawString(margin, height - margin - 95, f"*{order_id}*")
                c.setFont("Helvetica-Bold", 22)
                c.drawRightString(width - margin, height - margin - 95, f"Box: #{i+1}/{box_qty}")
                c.showPage()
            c.save()
            return filename
        except Exception:
            if os.path.exists(filename):
                os.remove(filename)
            raise

    def open_pdf_by_platform(path):
        import subprocess
        abs_path = os.path.abspath(path)
        try:
            if platform == "win":
                os.startfile(abs_path)
            elif platform == "darwin":
                subprocess.call(["open", abs_path])
            else:
                subprocess.call(["xdg-open", abs_path])
        except Exception as e:
            print("open_pdf error:", e)


else:  # Android
    from jnius import autoclass
    import socket
    from kivy.uix.spinner import Spinner

    def request_android_permissions():
        try:
            from android.permissions import request_permissions, Permission
            permissions = [
                Permission.CAMERA,
                Permission.BLUETOOTH,
                Permission.BLUETOOTH_ADMIN,
                Permission.BLUETOOTH_CONNECT,
                Permission.BLUETOOTH_SCAN,
                Permission.ACCESS_FINE_LOCATION
            ]
            request_permissions(permissions)
        except Exception as e:
            print("request_android_permissions error:", e)

    def escpos_bytes_for_label(order_id, customer, box_index, box_total, encoding='cp437'):
        b = bytearray()
        b += b'\x1b\x40'
        b += b'\x1b\x61\x00'
        b += b'\x1d\x21\x11' + order_id.encode(encoding, errors='replace') + b'\n'
        b += b'\x1d\x21\x01' + customer.encode(encoding, errors='replace') + b'\n'
        b += b'\x1d\x21\x00'
        b += b'\x1d\x6b\x49' + b'\x0d\x0a'
        b += order_id.encode(encoding, errors='replace') + b'\x00' + b'\n'
        b += b'\x1b\x61\x02'
        b += b'\x1d\x21\x11' + f"Box: #{box_index}/{box_total}".encode(encoding, errors='replace') + b'\n'
        b += b'\x1b\x61\x00'
        b += b'\x1d\x21\x00'
        b += b'\x1d\x56\x00'
        time.sleep(0.5)
        return bytes(b)

    def print_via_bluetooth_pyjnius(mac_addr, payload_bytes):
        try:
            UUID = autoclass('java.util.UUID')
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            adapter = BluetoothAdapter.getDefaultAdapter()
            device = adapter.getRemoteDevice(mac_addr)
            spp_uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB")
            socket = device.createRfcommSocketToServiceRecord(spp_uuid)
            if adapter.isDiscovering():
                adapter.cancelDiscovery()
            socket.connect()
            out = socket.getOutputStream()
            out.write(payload_bytes)
            out.flush()
            time.sleep(1.5)
            out.close()
            socket.close()
            return True, None
        except Exception as e:
            return False, str(e)

    def print_via_wifi_escpos(ip, port, payload_bytes, timeout=5):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((ip, port))
            s.sendall(payload_bytes)
            time.sleep(1.5)
            s.close()
            return True, None
        except Exception as e:
            return False, str(e)

    def find_paired_printers_pyjnius():
        try:
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            adapter = BluetoothAdapter.getDefaultAdapter()
            if adapter is None: 
                return []
            paired = adapter.getBondedDevices()
            devices = []
            try:
                arr = paired.toArray()
                for dev in arr:
                    devices.append((dev.getName(), dev.getAddress()))
            except:
                it = paired.iterator()
                while it.hasNext():
                    dev = it.next()
                    devices.append((dev.getName(), dev.getAddress()))
            return devices
        except Exception as e:
            print("find_paired_printers_pyjnius error:", e)
            return []


# ---------- A6 PAPER WIDGET ----------
class A6Paper(BoxLayout):
    def __init__(self, order_id, customer, box_index, box_total, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(280)
        self.padding = [dp(20), dp(20), dp(20), dp(20)]
        self.spacing = dp(15)
        
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
            Color(0, 0, 0, 1)
            self.border = Line(rectangle=(self.x, self.y, self.width, self.height), width=2)
        
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        self.order_label = Label(
            text=order_id,
            font_size=sp(42),
            size_hint_y=None,
            height=dp(95),
            halign='left',
            valign='middle',
            color=COLOR_BLACK,
            bold=True
        )
        self.order_label.bind(size=self.order_label.setter('text_size'))
        self.add_widget(self.order_label)
        
        self.customer_label = Label(
            text=customer,
            font_size=sp(28),
            size_hint_y=None,
            height=dp(60),
            halign='left',
            valign='middle',
            color=(0.2, 0.2, 0.2, 1)
        )
        self.customer_label.bind(size=self.customer_label.setter('text_size'))
        self.add_widget(self.customer_label)
        
        bottom_row = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(55), spacing=dp(15))
        
        self.barcode_label = Label(
            text=f"* {order_id} *",
            font_size=sp(18),
            size_hint_x=0.55,
            halign='left',
            valign='middle',
            color=COLOR_BLACK
        )
        self.barcode_label.bind(size=self.barcode_label.setter('text_size'))
        
        self.box_label = Label(
            text=f"Box: #{box_index}/{box_total}",
            font_size=sp(32),
            size_hint_x=0.45,
            halign='right',
            valign='middle',
            color=COLOR_BLACK,
            bold=True
        )
        self.box_label.bind(size=self.box_label.setter('text_size'))
        
        bottom_row.add_widget(self.barcode_label)
        bottom_row.add_widget(self.box_label)
        self.add_widget(bottom_row)
    
    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.border.rectangle = (self.x, self.y, self.width, self.height)


# ---------- SCANNER SCREEN ----------
class ScannerScreen(Screen):
    def __init__(self, callback=None, **kwargs):
        super().__init__(**kwargs)
        self.callback = callback
        
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # Header
        header = BoxLayout(size_hint_y=None, height=dp(50))
        back_btn = Button(text="←", font_size=dp(24), size_hint_x=None, width=dp(60))
        back_btn.bind(on_release=self.go_back)
        title = Label(text="SCAN BARCODE", font_size=dp(18), bold=True, color=COLOR_PRIMARY)
        header.add_widget(back_btn)
        header.add_widget(title)
        layout.add_widget(header)
        
        # ZBarCam - chỉ hoạt động trên Android
        if is_android():
            try:
                self.zbarcam = ZBarCam()
                layout.add_widget(self.zbarcam)
                # Theo dõi barcode
                Clock.schedule_interval(self.check_barcode, 0.5)
            except Exception as e:
                layout.add_widget(Label(text=f"Lỗi camera: {e}", color=COLOR_ERROR))
        else:
            layout.add_widget(Label(text="Scan chỉ hoạt động trên Android", color=COLOR_GRAY))
        
        # Kết quả
        self.result_label = Label(text="Đưa mã vạch vào khung hình", size_hint_y=None, height=dp(40))
        layout.add_widget(self.result_label)
        
        self.add_widget(layout)
    
    def check_barcode(self, dt):
        if hasattr(self, 'zbarcam') and self.zbarcam.symbols:
            barcode_data = self.zbarcam.symbols[0].data.decode('utf-8')
            self.result_label.text = f"✅ {barcode_data}"
            if self.callback:
                self.callback(barcode_data)
            Clock.schedule_once(lambda dt: self.go_back(), 1)
    
    def go_back(self, *args):
        if hasattr(self, 'check_barcode'):
            Clock.unschedule(self.check_barcode)
        self.manager.current = "home"


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.clearcolor = COLOR_BACKGROUND
        
        # Layout chính - dùng GridLayout để căn giữa
        main_layout = BoxLayout(orientation='vertical', padding=dp(30), spacing=dp(25))
        
        # Header
        header = Label(
            text="ORDER PRINTER",
            font_size=dp(32),
            size_hint_y=None,
            height=dp(70),
            color=COLOR_PRIMARY,
            bold=True
        )
        main_layout.add_widget(header)
        
        # Form container
        form_container = BoxLayout(orientation='vertical', spacing=dp(20), size_hint_y=None)
        form_container.bind(minimum_height=form_container.setter('height'))
        
        # === SO NUM ===
        so_label = Label(
            text="SO NUM",
            font_size=dp(16),
            size_hint_y=None,
            height=dp(25),
            halign='left',
            color=COLOR_GRAY,
            bold=True
        )
        so_label.bind(size=so_label.setter('text_size'))
        form_container.add_widget(so_label)
        
        so_row = BoxLayout(orientation='horizontal', spacing=dp(12), size_hint_y=None, height=dp(60))
        self.so_input = TextInput(
            text="",
            font_size=dp(20),
            multiline=False,
            background_color=COLOR_WHITE,
            foreground_color=COLOR_BLACK,
            size_hint_x=0.7,
            padding=[dp(15), dp(10), dp(15), dp(10)]
        )
        scan_btn = Button(
            text="SCAN",
            font_size=dp(16),
            size_hint_x=0.3,
            background_color=COLOR_PRIMARY,
            color=COLOR_WHITE,
            bold=True
        )
        scan_btn.bind(on_release=self.open_scanner)
        so_row.add_widget(self.so_input)
        so_row.add_widget(scan_btn)
        form_container.add_widget(so_row)
        
        # === NAME ===
        name_label = Label(
            text="NAME",
            font_size=dp(16),
            size_hint_y=None,
            height=dp(25),
            halign='left',
            color=COLOR_GRAY,
            bold=True
        )
        name_label.bind(size=name_label.setter('text_size'))
        form_container.add_widget(name_label)
        
        self.name_input = TextInput(
            text="",
            font_size=dp(20),
            multiline=False,
            background_color=COLOR_WHITE,
            foreground_color=COLOR_BLACK,
            size_hint_y=None,
            height=dp(60),
            padding=[dp(15), dp(10), dp(15), dp(10)]
        )
        form_container.add_widget(self.name_input)
        
        # === BOX ===
        box_label = Label(
            text="BOX",
            font_size=dp(16),
            size_hint_y=None,
            height=dp(25),
            halign='left',
            color=COLOR_GRAY,
            bold=True
        )
        box_label.bind(size=box_label.setter('text_size'))
        form_container.add_widget(box_label)
        
        self.box_input = TextInput(
            text="",
            font_size=dp(20),
            multiline=False,
            input_filter='int',
            background_color=COLOR_WHITE,
            foreground_color=COLOR_BLACK,
            size_hint_y=None,
            height=dp(60),
            padding=[dp(15), dp(10), dp(15), dp(10)]
        )
        form_container.add_widget(self.box_input)
        
        main_layout.add_widget(form_container)
        
        # === NÚT IN ĐƠN ===
        btn_print = Button(
            text="IN ĐƠN",
            font_size=dp(22),
            size_hint_y=None,
            height=dp(65),
            background_color=COLOR_SUCCESS,
            color=COLOR_WHITE,
            bold=True
        )
        btn_print.bind(on_release=self.on_print)
        main_layout.add_widget(btn_print)
        
        # === NÚT LỊCH SỬ ===
        btn_history = Button(
            text="LỊCH SỬ",
            font_size=dp(18),
            size_hint_y=None,
            height=dp(55),
            background_color=COLOR_GRAY,
            color=COLOR_WHITE
        )
        btn_history.bind(on_release=lambda *_: setattr(self.manager, "current", "history"))
        main_layout.add_widget(btn_history)
        
        self.add_widget(main_layout)
    
    def open_scanner(self, *args):
        if not is_android():
            Popup(title="Thông báo", 
                  content=Label(text="Tính năng scan chỉ hoạt động trên Android"), 
                  size_hint=(.8, .4)).open()
            return
        
        # Request camera permission
        if is_android():
            request_android_permissions()
        
        scanner_screen = ScannerScreen(callback=self.on_barcode_scanned, name="scanner")
        self.manager.add_widget(scanner_screen)
        self.manager.current = "scanner"
    
    def on_barcode_scanned(self, barcode_data):
        self.so_input.text = barcode_data
    
    def on_print(self, *_):
        oid = self.so_input.text.strip()
        cust = self.name_input.text.strip()
        box = self.box_input.text.strip()
        
        if not oid or not cust or not box:
            Popup(title="Thiếu thông tin", 
                  content=Label(text="Vui lòng nhập đầy đủ SO Num, Name và Box!"), 
                  size_hint=(.8, .4)).open()
            return
        
        try:
            box_n = int(box)
            if box_n <= 0:
                raise ValueError
        except:
            Popup(title="Sai định dạng", 
                  content=Label(text="Box phải là số nguyên dương"), 
                  size_hint=(.8, .4)).open()
            return
        
        if has_been_printed(oid):
            boxl = BoxLayout(orientation='vertical', spacing=dp(12))
            boxl.add_widget(Label(text=f"⚠️ Đơn hàng {oid} đã được in trước đó!\nCó chắc muốn in lại?"))
            btnl = BoxLayout(spacing=dp(12))
            popup = Popup(title="CẢNH BÁO ĐƠN TRÙNG", content=boxl, size_hint=(.8, .4))
            
            def yes(*_):
                popup.dismiss()
                self.do_print(oid, cust, box_n)
            
            def no(*_):
                popup.dismiss()
            
            btnl.add_widget(Button(text="CÓ, in lại", on_release=yes, background_color=COLOR_WARNING))
            btnl.add_widget(Button(text="KHÔNG", on_release=no))
            boxl.add_widget(btnl)
            popup.open()
            return
        
        self.do_print(oid, cust, box_n)
    
    def do_print(self, oid, cust, box_n):
        try:
            if not is_android():
                pdf_path = create_pdf_a6_landscape(oid, cust, box_n)
                add_history_entry(oid, cust, box_n)
                open_pdf_by_platform(pdf_path)
                Popup(title="Hoàn tất", 
                      content=Label(text=f"Đã tạo {pdf_path} và mở để in/kiểm tra."), 
                      size_hint=(.8, .4)).open()
            else:
                request_android_permissions()
                self.show_preview_and_print(oid, cust, box_n)
            
            self.so_input.text = ""
            self.name_input.text = ""
            self.box_input.text = ""
            
        except Exception as e:
            traceback.print_exc()
            Popup(title="Lỗi", content=Label(text=str(e)), size_hint=(.8, .4)).open()
    
    def show_preview_and_print(self, oid, cust, box_n):
        from kivy.uix.spinner import Spinner
        
        root = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
        
        header = Label(text=f"XEM TRƯỚC NHÃN ({box_n} thùng)", font_size=dp(16), bold=True, color=COLOR_BLACK, size_hint_y=None, height=dp(40))
        root.add_widget(header)
        
        scroll = ScrollView(size_hint=(1, 0.55), do_scroll_x=False, do_scroll_y=True)
        container = GridLayout(cols=1, spacing=dp(15), size_hint_y=None, padding=[dp(5), dp(5), dp(5), dp(5)])
        container.bind(minimum_height=container.setter('height'))
        
        for i in range(box_n):
            a6_paper = A6Paper(oid, cust, i+1, box_n)
            container.add_widget(a6_paper)
        
        scroll.add_widget(container)
        root.add_widget(scroll)
        
        if box_n > 1:
            hint = Label(text="↑ VUỐT DỌC ĐỂ XEM CÁC THÙNG ↑", font_size=dp(12), size_hint_y=None, height=dp(25), color=COLOR_GRAY)
            root.add_widget(hint)
        
        # Wi-Fi Print UI
        wifi_box = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(180), spacing=dp(6))
        
        printers = load_wifi_printers()
        printer_names = ["(Máy mới)"] + [p["name"] for p in printers]
        
        spinner = Spinner(text="(Máy mới)", values=printer_names, size_hint_y=None, height=dp(44))
        ip_input = TextInput(hint_text="IP máy in", font_size=14, multiline=False, size_hint_y=None, height=dp(44))
        port_input = TextInput(hint_text="Cổng (port)", font_size=14, input_filter='int', multiline=False, size_hint_y=None, height=dp(44))
        
        def on_printer_select(spinner, text):
            if text == "(Máy mới)":
                ip_input.text = ""
                port_input.text = ""
            else:
                sel = next((p for p in printers if p["name"] == text), None)
                if sel:
                    ip_input.text = sel["ip"]
                    port_input.text = str(sel["port"])
        
        spinner.bind(text=on_printer_select)
        
        wifi_box.add_widget(spinner)
        wifi_box.add_widget(ip_input)
        wifi_box.add_widget(port_input)
        root.add_widget(wifi_box)
        
        status = Label(text="", size_hint_y=None, height=dp(30), color=COLOR_BLACK, font_size=dp(12))
        root.add_widget(status)
        
        btn_row = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))
        btn_print_bt = Button(text="In Bluetooth", font_size=14, background_color=COLOR_PRIMARY, color=COLOR_WHITE)
        btn_print_wifi = Button(text="In Wi-Fi", font_size=14, background_color=COLOR_SUCCESS, color=COLOR_WHITE)
        btn_cancel = Button(text="Hủy", font_size=14, background_color=COLOR_GRAY, color=COLOR_WHITE)
        btn_row.add_widget(btn_print_bt)
        btn_row.add_widget(btn_print_wifi)
        btn_row.add_widget(btn_cancel)
        root.add_widget(btn_row)
        
        popup = Popup(title="In nhãn A6", content=root, size_hint=(.95, .9))
        
        def do_bt_print(*_):
            devices = find_paired_printers_pyjnius()
            if not devices:
                status.text = "❌ Không tìm thấy thiết bị Bluetooth"
                status.color = COLOR_ERROR
                return
            status.text = "🖨️ Đang in..."
            status.color = COLOR_PRIMARY
            for i in range(box_n):
                payload = escpos_bytes_for_label(oid, cust, i+1, box_n)
                ok, err = print_via_bluetooth_pyjnius(devices[0][1], payload)
                if not ok:
                    status.text = f"❌ Lỗi BT: {err}"
                    status.color = COLOR_ERROR
                    return
                time.sleep(1)
            add_history_entry(oid, cust, box_n)
            status.text = f"✅ Đã in {box_n} nhãn qua Bluetooth"
            status.color = COLOR_SUCCESS
            from threading import Timer
            Timer(2, popup.dismiss).start()
        
        def do_wifi_print(*_):
            ip = ip_input.text.strip()
            port = port_input.text.strip()
            
            if not ip or not port:
                status.text = "⚠️ Nhập IP & Port!"
                status.color = COLOR_WARNING
                return
            
            try:
                port_n = int(port)
            except:
                status.text = "⚠️ Port không hợp lệ!"
                status.color = COLOR_ERROR
                return
            
            add_wifi_printer(f"{ip}:{port}", ip, port_n)
            
            status.text = "📡 Đang in qua Wi-Fi..."
            status.color = COLOR_PRIMARY
            for i in range(box_n):
                payload = escpos_bytes_for_label(oid, cust, i+1, box_n)
                ok, err = print_via_wifi_escpos(ip, port_n, payload)
                if not ok:
                    status.text = f"❌ Lỗi Wi-Fi: {err}"
                    status.color = COLOR_ERROR
                    return
                time.sleep(1)
            
            add_history_entry(oid, cust, box_n)
            status.text = f"✅ Đã in {box_n} nhãn qua Wi-Fi ({ip}:{port})"
            status.color = COLOR_SUCCESS
            from threading import Timer
            Timer(2, popup.dismiss).start()
        
        btn_print_bt.bind(on_release=do_bt_print)
        btn_print_wifi.bind(on_release=do_wifi_print)
        btn_cancel.bind(on_release=lambda *_: popup.dismiss())
        popup.open()


# ---------- HISTORY SCREEN ----------
class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))
        
        header = Label(text="LỊCH SỬ IN", font_size=dp(22), bold=True, size_hint_y=None, height=dp(50), color=COLOR_PRIMARY)
        root.add_widget(header)
        
        scroll = ScrollView()
        self.container = GridLayout(cols=1, spacing=dp(5), size_hint_y=None)
        self.container.bind(minimum_height=self.container.setter('height'))
        scroll.add_widget(self.container)
        root.add_widget(scroll)
        
        btn_back = Button(text="← VỀ TRANG CHỦ", size_hint_y=None, height=dp(50), font_size=dp(16), background_color=COLOR_GRAY, color=COLOR_WHITE)
        btn_back.bind(on_release=lambda *_: setattr(self.manager, "current", "home"))
        root.add_widget(btn_back)
        
        self.add_widget(root)
    
    def on_enter(self, *args):
        self.refresh_history()
    
    def refresh_history(self):
        self.container.clear_widgets()
        data = load_history()
        
        counts = {}
        for it in data:
            oid = it.get("order_id")
            counts[oid] = counts.get(oid, 0) + 1
        
        for it in reversed(data):
            oid = it.get("order_id", "?")
            cust = it.get("customer", "?")
            box_qty = it.get("box_qty", 0)
            timestamp = it.get("timestamp", "")
            
            try:
                date_str = datetime.fromisoformat(timestamp).strftime("%d/%m/%Y %H:%M")
            except:
                date_str = timestamp[:16]
            
            is_duplicate = counts.get(oid, 0) > 1
            text_color = COLOR_ERROR if is_duplicate else COLOR_BLACK
            text = f"{oid}  |  {cust}  |  {box_qty} box  |  {date_str}"
            
            row = BoxLayout(size_hint_y=None, height=dp(45), padding=[dp(10), 0, dp(10), 0])
            lbl = Label(text=text, font_size=dp(14), color=text_color, halign='left', valign='middle')
            lbl.bind(size=lbl.setter('text_size'))
            row.add_widget(lbl)
            self.container.add_widget(row)


# ---------- MAIN APP ----------
class OrderPrinterApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(HistoryScreen(name="history"))
        return sm


if __name__ == "__main__":
    OrderPrinterApp().run()