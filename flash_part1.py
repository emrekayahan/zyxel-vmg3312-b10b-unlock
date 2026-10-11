import serial
import socket
import time
import os
import sys

COM_PORT = 'COM4'
BAUD = 115200
FW_PATH = r'c:\Users\Derin&Deniz\Downloads\modem\firmware\100AAPP2D0.bin'
MODEM_IP = '192.168.1.1'
LOCAL_IP = '192.168.1.100'

print("="*60)
print("[*] PARTITION 1 FLAŞLAMA VE TÜRK TELEKOM'U TAMAMEN SİLME İŞLEMİ")
print(f"[*] Firmware: {FW_PATH} ({os.path.getsize(FW_PATH)} bytes)")
print("="*60)
sys.stdout.flush()

ser = serial.Serial(COM_PORT, BAUD, timeout=0.1)

# CFE'de fwselect 1 ayarla
print("[*] CFE'de Partition 1 seciliyor...")
ser.write(b'\r\n')
time.sleep(0.2)
ser.write(b'fwselect 1\r\n')
time.sleep(0.5)
out = ser.read(ser.in_waiting).decode('latin1', errors='replace')
print("CFE:", out.strip())

# Firmware oku
with open(FW_PATH, 'rb') as f:
    fw_data = f.read()

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

print(f"[*] Firmware HTTP uzerinden CFE'ye gonderiliyor ({content_length} bayt)...")
sys.stdout.flush()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(15)
s.bind((LOCAL_IP, 0))
s.connect((MODEM_IP, 80))
s.sendall(http_request)
s.close()
print("[+] Firmware aktarimi tamamlandi! Flash yazma basladi...")
sys.stdout.flush()

start_flash = time.time()
while time.time() - start_flash < 180:
    if ser.in_waiting:
        chunk = ser.read(ser.in_waiting).decode('latin1', errors='replace')
        sys.stdout.write(chunk)
        sys.stdout.flush()
        if 'Image flash done' in chunk:
            print("\n\n[!!!] TEBRIKLER! PARTITION 1 BASARIYLA YAZILDI! [!!!]")
    time.sleep(0.05)

ser.close()
print("\n[*] Script bitti.")
