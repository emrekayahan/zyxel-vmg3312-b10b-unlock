import serial
import time
import sys

COM_PORT = 'COM4'
BAUD = 115200

ser = serial.Serial(COM_PORT, BAUD, timeout=0.1)

print("[*] CLI Kilit kalkmasi bekleniyor...")
while True:
    ser.write(b'\r\n')
    time.sleep(1)
    if ser.in_waiting:
        txt = ser.read(ser.in_waiting).decode('latin1', errors='replace')
        if 'Login:' in txt and 'Authorization failed' not in txt:
            print("[+] Temiz Login ekrani yakalandi!")
            break
        else:
            print(".", end='', flush=True)

# Login
ser.write(b'admin\r\n')
time.sleep(0.5)
ser.read(ser.in_waiting)

ser.write(b'turktelekom\r\n')
time.sleep(1)
out = ser.read(ser.in_waiting).decode('latin1', errors='replace')
print("\nLogin Yaniti:\n", out)

if '>' in out:
    print("[+] OTURUM BASARIYLA ACILDI!")
    
    commands = [
        'sys atsh',
        'webstyle',
        'webstyle help',
        'AutoFWcli',
        'romctrl'
    ]
    
    for cmd in commands:
        print(f"\n--- Komut: {cmd} ---")
        ser.write(cmd.encode() + b'\r\n')
        time.sleep(0.8)
        resp = ser.read(ser.in_waiting).decode('latin1', errors='replace')
        print(resp.strip())

ser.close()
