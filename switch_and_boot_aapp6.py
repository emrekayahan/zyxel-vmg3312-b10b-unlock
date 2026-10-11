import serial
import time
import sys

COM_PORT = 'COM4'
BAUD = 115200

print("="*60)
print("[*] PARTITION 0 (AAPP.6) AKTIFLESTIRME VE AKILLI KORUMA")
print("="*60)

ser = serial.Serial(COM_PORT, BAUD, timeout=0.05)

# 1. Login ekrani gelene kadar bekle
print("[*] Temiz Login ekrani bekleniyor...")
while True:
    ser.write(b'\r\n')
    time.sleep(1)
    if ser.in_waiting:
        txt = ser.read(ser.in_waiting).decode('latin1', errors='replace')
        if 'Login:' in txt and 'Authorization failed' not in txt and 'Password:' not in txt:
            print("\n[+] Temiz Login ekrani yakalandi!")
            break
        elif '>' in txt:
            print("\n[+] Zaten CLI acik!")
            break
        else:
            print(".", end='', flush=True)

# Oturum ac
if '>' not in txt:
    ser.write(b'admin\r\n')
    time.sleep(0.5)
    ser.read(ser.in_waiting)
    ser.write(b'turktelekom\r\n')
    time.sleep(1)
    out = ser.read(ser.in_waiting).decode('latin1', errors='replace')
    print("Login yaniti:", repr(out))
    if '>' not in out:
        print("[-] CLI girisi basarisiz!")
        ser.close()
        sys.exit(1)

print("[+] CLI OTURUMU ACILDI!")

# fwselect 0 gonder
print("[*] 'sys fwselect 0' komutu gonderiliyor...")
ser.write(b'sys fwselect 0\r\n')
time.sleep(1)
resp1 = ser.read(ser.in_waiting).decode('latin1', errors='replace')
print("fwselect yaniti:\n", resp1.strip())

# reboot gonder
print("[*] 'reboot' komutu gonderiliyor...")
ser.write(b'reboot\r\n')
time.sleep(1)

# Boot surecini izle
print("\n[*] Acilis sureci izleniyor (AAPP.6 test ediliyor)...")
start = time.time()
panic = False
success = False

while time.time() - start < 45:
    if ser.in_waiting:
        txt = ser.read(ser.in_waiting).decode('latin1', errors='replace')
        sys.stdout.write(txt)
        sys.stdout.flush()
        
        if 'Kernel panic' in txt or 'Oops[' in txt or 'kerSysMipsSoftReset' in txt:
            print("\n\n[!] DIKKAT: AAPP.6 CEKIRDEK COKMESI (KERNEL PANIC) VERDI!")
            panic = True
            break
            
        if 'Release Version' in txt and '191117' not in txt:
            print("\n\n[SUCCESS] TEBRIKLER! AAPP.6 BASARIYLA ACILDI!")
            success = True
            break
            
    time.sleep(0.02)

# Eger cokerse CFE'yi yakala ve Partition 1'e al
if panic:
    print("\n[!!!] GUVENLIK SISTEMI: MODEM BRICK KALMAYACAK! [!!!]")
    print("[*] CFE Bootloader yakalaniyor...")
    start_rec = time.time()
    while time.time() - start_rec < 30:
        ser.write(b' \r\n')
        if ser.in_waiting:
            txt = ser.read(ser.in_waiting).decode('latin1', errors='replace')
            if 'CFE>' in txt:
                print("\n[+] CFE YAKALANDI! fwselect 1 ile calisan bolum seciliyor...")
                ser.write(b'fwselect 1\r\n')
                time.sleep(0.5)
                ser.write(b'ATGO\r\n')
                print("[+] MODEM GUVENLE SAGLAM BOLUME GERI ALINDI!")
                break
        time.sleep(0.01)

ser.close()
print("\n[*] Islem tamamlandi.")
