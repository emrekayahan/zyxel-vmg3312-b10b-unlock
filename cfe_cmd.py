import serial
import time
import sys

COM_PORT = 'COM4'
BAUD = 115200

print("="*60)
print("[*] CFE KONTROL VE KOMUT ARACI")
print("[*] LUTFEN MODEMI POWER TUSUNDAN KAPATIP ACIN...")
print("="*60)
sys.stdout.flush()

ser = serial.Serial(COM_PORT, BAUD, timeout=0.01)

start = time.time()
caught = False
while time.time() - start < 120:
    ser.write(b' \r\n')
    if ser.in_waiting:
        chunk = ser.read(ser.in_waiting).decode('latin1', errors='replace')
        sys.stdout.write(chunk)
        sys.stdout.flush()
        if 'CFE>' in chunk:
            print("\n\n[+] CFE YAKALANDI!")
            caught = True
            break
    time.sleep(0.01)

if not caught:
    print("\n[-] CFE yakalanamadi.")
    ser.close()
    sys.exit(1)

time.sleep(0.5)
# help gonder
print("\n[*] CFE 'help' komutu gonderiliyor...")
ser.write(b'help\r\n')
time.sleep(1)
if ser.in_waiting:
    out = ser.read(ser.in_waiting).decode('latin1', errors='replace')
    print(out)

# CFE interaktif modda beklesin
print("\n[+] CFE komut modunda hazir bekliyor.")
ser.close()
