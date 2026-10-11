import socket
import struct
import time
import os
import sys

MODEM_IP = "192.168.1.1"
TFTP_PORT = 69
LOCAL_IP = "192.168.1.100"
FIRMWARE_FILE = r"c:\Users\Derin&Deniz\Downloads\modem\firmware\100AAPP7D0.bin"

with open(FIRMWARE_FILE, "rb") as f:
    FW_DATA = f.read()

BLOCK_SIZE = 512
total_blocks = (len(FW_DATA) + BLOCK_SIZE - 1) // BLOCK_SIZE

print(f"[*] Firmware yuklendi: {len(FW_DATA)} bayt ({total_blocks} blok)")
print(f"[*] Pusuya yatildi... Modem ({MODEM_IP}) ping verdigi anda TFTP ile gonderilecek.")
print("[*] Lutfen modemi Power tusundan kapatip acin veya resetleyerek donguye sokun...")

def ping_modem():
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP) if False else None
    # TCP port 80 veya UDP 69 uzerinden CFE yoklama
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.1)
    try:
        sock.bind((LOCAL_IP, 0))
        # TFTP Read/Write Request probe
        wrq = b"\x00\x02vmlinux\x00octet\x00"
        sock.sendto(wrq, (MODEM_IP, TFTP_PORT))
        data, addr = sock.recvfrom(1024)
        sock.close()
        return True, addr
    except Exception:
        sock.close()
        return False, None

# Sürekli TFTP WRQ gönderen döngü
attempt = 0
while True:
    attempt += 1
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(0.3)
    try:
        sock.bind((LOCAL_IP, 0))
        # Opcode 2 = WRQ (Write Request)
        wrq = b"\x00\x02ras.bin\x00octet\x00"
        sock.sendto(wrq, (MODEM_IP, TFTP_PORT))
        resp, srv_addr = sock.recvfrom(1024)
        
        # Opcode 4 = ACK
        opcode, block_num = struct.unpack("!HH", resp[:4])
        if opcode == 4 and block_num == 0:
            print(f"\n[!!!] CFE TFTP CEVAP VERDI! Sunucu adresi: {srv_addr}")
            print("[*] Firmware yukleniyor... MODEMI ASLA KAPATMAYIN!")
            
            # Bloklari gonder
            for b in range(1, total_blocks + 1):
                start = (b - 1) * BLOCK_SIZE
                end = start + BLOCK_SIZE
                chunk = FW_DATA[start:end]
                
                # DATA paketi: Opcode 3 + Block Num
                pkt = struct.pack("!HH", 3, b % 65536) + chunk
                
                # ACK bekleme
                retries = 5
                while retries > 0:
                    sock.sendto(pkt, srv_addr)
                    try:
                        ack, _ = sock.recvfrom(1024)
                        ack_op, ack_b = struct.unpack("!HH", ack[:4])
                        if ack_op == 4 and ack_b == (b % 65536):
                            break
                    except socket.timeout:
                        retries -= 1
                
                if b % 500 == 0 or b == total_blocks:
                    print(f"[*] Ilerleme: %{b * 100 // total_blocks} ({b}/{total_blocks} blok)")
            
            print("\n[SUCCESS] Firmware basariyla gonderildi! Modem flash yaziyor, 2-3 dakika bekleyin...")
            sock.close()
            sys.exit(0)
    except Exception:
        pass
    finally:
        sock.close()
    
    if attempt % 20 == 0:
        print(f"[*] Yoklaniyor... (Deneme {attempt}) - Modemi kapatip acabilirsiniz.")
    time.sleep(0.05)
