import subprocess
import time
import re
import os

MODEM_IP = "192.168.1.3"
PASSWORD = "turktelekom1"
FW_PATH = os.path.abspath("firmware/100AAPP7D0.bin")

def attempt_upgrade():
    print("[*] Modem oturumunun serbest kalmasi kontrol ediliyor...")
    
    max_wait = 300  # 5 minutes
    start = time.time()
    
    while time.time() - start < max_wait:
        # Check login
        cmd_login = [
            'curl.exe', '-s', '-i',
            '-c', 'cookie.txt',
            '-b', 'cookie.txt',
            '-d', f'AuthName=admin&AuthPassword={PASSWORD}',
            f'http://{MODEM_IP}/login/login-page.cgi'
        ]
        res = subprocess.run(cmd_login, capture_output=True, text=True)
        out = res.stdout
        
        if "A user exist" in out:
            elapsed = int(time.time() - start)
            print(f"[*] Onceki oturum henuz zaman asimina ugramadi ({elapsed}s gecti). 10 saniye sonra tekrar deneniyor...")
            time.sleep(10)
            continue
        elif "top.location='/index.html'" in out or "SESSION=" in out:
            print("[+] Oturum basariyla acildi!")
            break
        else:
            print(f"[-] Beklenmeyen yanit: {out[:200]}")
            time.sleep(10)
    else:
        print("[-] 5 dakika icinde oturum serbest kalmadi.")
        return False

    print(f"[*] Firmware yukleniyor ({FW_PATH})...")
    cmd_upload = [
        'curl.exe', '-i',
        '-b', 'cookie.txt',
        '-e', f'http://{MODEM_IP}/pages/maintenance/firmwareUpgrade/firmwareUpgrade.html',
        '-F', f'filename=@{FW_PATH}',
        '-F', 'upload_btn=Yükle',
        f'http://{MODEM_IP}/pages/tabFW/firmwareUpgrade-upload.cgi'
    ]
    
    print("[*] Yukleme komutu calistiriliyor...")
    up_res = subprocess.run(cmd_upload, capture_output=True, text=True)
    print("[*] Yukleme sonucu:")
    print(up_res.stdout[:500] if up_res.stdout else "(Cikti yok)")
    print(up_res.stderr[:500] if up_res.stderr else "")
    
    print("[+] Firmware gonderildi! Modem yeniden baslatiliyor...")
    return True

if __name__ == '__main__':
    attempt_upgrade()
