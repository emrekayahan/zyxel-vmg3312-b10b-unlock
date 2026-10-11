import serial
import socket
import time
import os
import sys

COM_PORT = 'COM4'
BAUD = 115200
FW_PATH = r'c:\Users\Derin&Deniz\Downloads\modem\firmware\100AAPP6D0.bin'
MODEM_IP = '192.168.1.1'
LOCAL_IP = '192.168.1.100'

print("="*60)
print("[*] GUVENLI AAPP.6 FLASLAMA VE OTOMATIK KURTARMA SISTEMI")
print(f"[*] Firmware: {FW_PATH} ({os.path.getsize(FW_PATH)} bytes)")
print("="*60)
sys.stdout.flush()

ser = serial.Serial(COM_PORT, BAUD, timeout=0.01)

# 1. Modeme reboot gonder
print("[*] Seri konsoldan reboot gonderiliyor...")
ser.write(b'\r\nreboot\r\n\r\n')
time.sleep(0.5)

# 2. CFE'yi yakala
print("[*] CFE Bootloader yakalaniyor (Lutfen bekleyin)...")
start = time.time()
cfe_caught = False
while time.time() - start < 60:
    ser.write(b' \r\n')
    if ser.in_waiting:
        txt = ser.read(ser.in_waiting).decode('latin1', errors='replace')
        sys.stdout.write(txt)
        sys.stdout.flush()
        if 'CFE>' in txt:
            print("\n[+] CFE YAKALANDI!")
            cfe_caught = True
            break
    time.sleep(0.01)

if not cfe_caught:
    print("[-] CFE zaman asimi!")
    ser.close()
    sys.exit(1)

time.sleep(1)

# 3. HTTP uzerinden AAPP.6 yukle
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

print(f"[*] Firmware CFE Web Kurtarma uzerinden aktariliyor ({content_length} bayt)...")
uploaded = False
for attempt in range(5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(15)
        s.bind((LOCAL_IP, 0))
        s.connect((MODEM_IP, 80))
        s.sendall(http_request)
        print("[+] Firmware aktarimi tamamlandi!")
        uploaded = True
        s.close()
        break
    except Exception as e:
        print(f"[*] Baglanti bekleniyor ({attempt+1}): {e}")
        time.sleep(1)

# 4. Flash yazma surecini izle
print("\n[*] Flash belleğe yazılıyor (Lütfen bekleyin, dokunmayın)...")
start_flash = time.time()
while time.time() - start_flash < 120:
    if ser.in_waiting:
        txt = ser.read(ser.in_waiting).decode('latin1', errors='replace')
        sys.stdout.write(txt)
        sys.stdout.flush()
        if 'Image flash done' in txt:
            print("\n[+] Flaş yazma işlemi başarıyla bitti! Reboot bekleniyor...")
            break
    time.sleep(0.05)

# 5. Açılış kontrolü ve çökme koruması
print("\n[*] Acilis kontrol ediliyor (AAPP.6 test ediliyor)...")
start_boot = time.time()
panic_detected = False
while time.time() - start_boot < 40:
    if ser.in_waiting:
        txt = ser.read(ser.in_waiting).decode('latin1', errors='replace')
        sys.stdout.write(txt)
        sys.stdout.flush()
        if 'Kernel panic' in txt or 'Oops[' in txt or 'kerSysMipsSoftReset' in txt:
            print("\n[!] DIKKAT: AAPP.6 SURUMUNDE KERNEL PANIC TESPIT EDILDI!")
            panic_detected = True
            break
        if 'Release Version' in txt and 'AAPP.6' in txt:
            print("\n[SUCCESS] TEBRIKLER! AAPP.6 BASARIYLA ACILDI!")
    time.sleep(0.05)

# 6. Eger cokerse CFE'yi aninda yakalayip Partition 1 (AAPP.12)'ye geri al
if panic_detected:
    print("\n[*] OTOMATIK KURTARMA: Calisan Partition 1'e geri donuluyor...")
    cfe_recovery = False
    start_rec = time.time()
    while time.time() - start_rec < 30:
        ser.write(b' \r\n')
        if ser.in_waiting:
            txt = ser.read(ser.in_waiting).decode('latin1', errors='replace')
            if 'CFE>' in txt:
                print("\n[+] CFE YAKALANDI! Partition 1 seciliyor...")
                ser.write(b'fwselect 1\r\n')
                time.sleep(0.5)
                ser.write(b'ATGO\r\n')
                cfe_recovery = True
                print("[+] Modem guvenle calisan AAPP.12 durumuna geri alindi!")
                break
        time.sleep(0.01)

ser.close()
print("\n[*] Islem tamamlandi.")
