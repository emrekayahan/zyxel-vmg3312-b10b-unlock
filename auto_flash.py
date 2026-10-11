import serial
import time
import sys
import socket
import os

COM_PORT = 'COM4'
BAUD = 115200
FW_PATH = r'c:\Users\Derin&Deniz\Downloads\modem\firmware\100AAPP2D0.bin'
MODEM_IP = '192.168.1.1'
LOCAL_IP = '192.168.1.100'

print("="*60)
print("[*] TAM OTOMATIK CFE FLAŞLAYICI VE OZGURLESTIRICI BASLADI")
print(f"[*] Hedef Global/Ozgun Firmware: {FW_PATH} ({os.path.getsize(FW_PATH)} bayt)")
print("="*60)

with open(FW_PATH, 'rb') as f:
    fw_data = f.read()

ser = serial.Serial(COM_PORT, BAUD, timeout=0.01)

print("\n[>>>] LUTFEN MODEMI SIMDI ARKASINDAKI POWER TUSUNDAN KAPATIP ACIN! [<<<]\n")
sys.stdout.flush()

# CFE'yi yakala
start = time.time()
cfe_caught = False
while time.time() - start < 180:
    ser.write(b' \r\n')
    if ser.in_waiting:
        chunk = ser.read(ser.in_waiting).decode('latin1', errors='replace')
        sys.stdout.write(chunk)
        sys.stdout.flush()
        if 'CFE>' in chunk:
            print("\n\n[!!!] CFE YAKALANDI! ISLEM BASLIYOR... [!!!]")
            cfe_caught = True
            break
    time.sleep(0.01)

if not cfe_caught:
    print("[-] CFE zaman asimi!")
    ser.close()
    sys.exit(1)

# CFE Web Server'ın IP ve Portunu hazırla
time.sleep(1)
print("\n[*] CFE Web Server test ediliyor...")

# HTTP POST ile firmware basma (Multipart form-data)
boundary = "---------------------------7e12e12a02b6"
content_type = f"multipart/form-data; boundary={boundary}"

header_part = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="filename"; filename="{os.path.basename(FW_PATH)}"\r\n'
    f"Content-Type: application/octet-stream\r\n\r\n"
).encode('ascii')

footer_part = f"\r\n--{boundary}--\r\n".encode('ascii')
content_length = len(header_part) + len(fw_data) + len(footer_part)

http_request = (
    f"POST /upload.cgi HTTP/1.1\r\n"
    f"Host: {MODEM_IP}\r\n"
    f"Content-Type: {content_type}\r\n"
    f"Content-Length: {content_length}\r\n"
    f"Connection: close\r\n\r\n"
).encode('ascii') + header_part + fw_data + footer_part

print(f"[*] Firmware HTTP uzerinden CFE'ye aktariliyor ({content_length} bayt)...")
uploaded = False
for attempt in range(5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(15)
        s.bind((LOCAL_IP, 0))
        s.connect((MODEM_IP, 80))
        s.sendall(http_request)
        print("[+] Firmware CFE'ye basariyla gonderildi!")
        uploaded = True
        s.close()
        break
    except Exception as e:
        print(f"[*] Baglanti bekleniyor (Deneme {attempt+1}): {e}")
        time.sleep(1)

# Konsoldan flash yazma logunu dinle
print("\n[*] Flaş yazma sureci seri konsoldan takip ediliyor (MODEME DOKUNMAYIN)...")
start_flash = time.time()
while time.time() - start_flash < 180:
    if ser.in_waiting:
        log_chunk = ser.read(ser.in_waiting).decode('latin1', errors='replace')
        sys.stdout.write(log_chunk)
        sys.stdout.flush()
    time.sleep(0.05)

ser.close()
print("\n[SUCCESS] Islem tamamlandi!")
