import serial
import time
import sys

COM_PORT = 'COM4'
BAUD = 115200

print("="*60)
print("[*] AAPP.6 FORCING AND FAIL-SAFE MONITOR")
print("="*60)
sys.stdout.flush()

ser = serial.Serial(COM_PORT, BAUD, timeout=0.01)

# 1. Login olana kadar bekle
print("[*] Sistem acilisi ve Login ekrani bekleniyor...")
while True:
    ser.write(b'\r\n')
    time.sleep(1)
    if ser.in_waiting:
        txt = ser.read(ser.in_waiting).decode('latin1', errors='replace')
        if 'Login:' in txt:
            print("[+] Login ekrani yakalandi!")
            break
        elif '>' in txt:
            print("[+] Zaten oturum acik!")
            break
        else:
            print(".", end='', flush=True)

# Oturum ac
ser.write(b'admin\r\n')
time.sleep(0.3)
ser.read(ser.in_waiting)
ser.write(b'turktelekom\r\n')
time.sleep(0.5)
out = ser.read(ser.in_waiting).decode('latin1', errors='replace')
print("\nOturum durumu:", repr(out))

# 2. Partition 0 sec (100AAPP6D0)
print("\n[*] 'sys fwselect 0' komutu gonderiliyor...")
ser.write(b'sys fwselect 0\r\n')
time.sleep(1)
resp1 = ser.read(ser.in_waiting).decode('latin1', errors='replace')
print("fwselect yaniti:", resp1.strip())

# 3. Reboot gonder
print("\n[*] 'sys reboot' komutu gonderiliyor...")
ser.write(b'sys reboot\r\n')
time.sleep(1)
resp2 = ser.read(ser.in_waiting).decode('latin1', errors='replace')
print("reboot yaniti:", resp2.strip())

# 4. AAPP.6 acilisini izle ve cokerse kurtar
print("\n[*] CFE ve AAPP.6 baslatiliyor, izleniyor...")
start_mon = time.time()
panic = False
success = False

while time.time() - start_mon < 60:
    if ser.in_waiting:
        txt = ser.read(ser.in_waiting).decode('latin1', errors='replace')
        sys.stdout.write(txt)
        sys.stdout.flush()
        
        if 'Kernel panic' in txt or 'Oops[' in txt or 'kerSysMipsSoftReset' in txt:
            print("\n\n[!] DIKKAT: AAPP.6 KERNEL PANIC VERDI!")
            panic = True
            break
            
        if 'Release Version' in txt and 'AAPP.6' in txt:
            print("\n\n[SUCCESS] TEBRIKLER! 100AAPP6D0 BASARIYLA ACILDI!")
            success = True
            break
            
    time.sleep(0.02)

# 5. Eger cokerse ANINDA CFE'yi yakala ve Partition 1'e geri al!
if panic:
    print("\n[!!!] GUVENLIK PROTOKOLU DEVREDE: MODEM BRICK KALMAYACAK! [!!!]")
    print("[*] CFE Bootloader yakalaniyor...")
    start_rec = time.time()
    while time.time() - start_rec < 30:
        ser.write(b' \r\n')
        if ser.in_waiting:
            txt = ser.read(ser.in_waiting).decode('latin1', errors='replace')
            if 'CFE>' in txt:
                print("\n[+] CFE YAKALANDI! fwselect 1 ile saglam bolum seciliyor...")
                ser.write(b'fwselect 1\r\n')
                time.sleep(0.5)
                ser.write(b'ATGO\r\n')
                print("[+] MODEM GUVENLE CALISAN AAPP.12 BOLUMUNE GERI ALINDI!")
                break
        time.sleep(0.01)

ser.close()
print("\n[*] Program tamamlandi.")
