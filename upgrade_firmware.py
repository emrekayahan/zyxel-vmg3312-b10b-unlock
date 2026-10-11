import urllib.request
import http.cookiejar
import os
import sys
import time

MODEM_IP = "192.168.1.3"
USERNAME = "admin"
PASSWORD = "turktelekom1"
FIRMWARE_FILE = os.path.join("firmware", "100AAPP7D0.bin")

def upload_firmware():
    if not os.path.exists(FIRMWARE_FILE):
        print(f"[-] Firmware dosyasi bulunamadi: {FIRMWARE_FILE}")
        return False

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    print(f"[*] Modeme baglaniliyor ({MODEM_IP})...")
    login_data = f"AuthName={USERNAME}&AuthPassword={PASSWORD}".encode('utf-8')
    login_req = urllib.request.Request(
        f"http://{MODEM_IP}/login/login-page.cgi",
        data=login_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    try:
        res = opener.open(login_req)
        body = res.read().decode('utf-8', errors='ignore')
        if "A user exist" in body:
            print("[-] HATA: Modem arayuzu su an tarayicinizda acik oldugu icin modem baska oturuma izin vermiyor ('A user exist').")
            print("[-] Lutfen tarayicinizdaki 192.168.1.3 sekmesini kapatin ve 2-3 dakika bekleyin.")
            return False
        print("[+] Oturum basariyla acildi!")
    except Exception as e:
        print(f"[-] Giris hatasi: {e}")
        return False

    # Read firmware binary
    fw_size = os.path.getsize(FIRMWARE_FILE)
    print(f"[*] Firmware dosyasi okunuyor: {FIRMWARE_FILE} ({fw_size / (1024*1024):.2f} MB)...")
    with open(FIRMWARE_FILE, 'rb') as f:
        fw_bytes = f.read()

    boundary = '----WebKitFormBoundaryUpGrAdE7D0bIn'
    body_parts = []
    body_parts.append(f'--{boundary}\r\n'.encode('ascii'))
    body_parts.append(f'Content-Disposition: form-data; name="filename"; filename="{os.path.basename(FIRMWARE_FILE)}"\r\n'.encode('ascii'))
    body_parts.append(b'Content-Type: application/octet-stream\r\n\r\n')
    body_parts.append(fw_bytes)
    body_parts.append(b'\r\n')
    body_parts.append(f'--{boundary}\r\n'.encode('ascii'))
    body_parts.append(b'Content-Disposition: form-data; name="upload_btn"\r\n\r\n')
    body_parts.append(b'Y\xc3\xbckle\r\n')
    body_parts.append(f'--{boundary}--\r\n'.encode('ascii'))

    payload = b''.join(body_parts)

    print(f"[*] Firmware modeme yukleniyor (/pages/tabFW/firmwareUpgrade-upload.cgi)... Bu islem 30-60 saniye surebilir...")
    upload_req = urllib.request.Request(
        f"http://{MODEM_IP}/pages/tabFW/firmwareUpgrade-upload.cgi",
        data=payload,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Referer": f"http://{MODEM_IP}/pages/maintenance/firmwareUpgrade/firmwareUpgrade.html"
        }
    )

    try:
        up_res = opener.open(upload_req, timeout=120)
        resp_text = up_res.read().decode('utf-8', errors='ignore')
        print("[+] Firmware basariyla gonderildi!")
        print("[+] Modem su anda firmware'i flash'a yaziyor ve yeniden baslatilacak (yaklasik 3-4 dakika surer).")
        print("[!] UYARI: Lutfen bu sirada modemin elektrigini veya kablosunu KESMEYIN.")
        return True
    except Exception as e:
        print(f"[-] Yukleme sirasinda durum: {e}")
        # Note: Often during reboot the connection resets or closes, which is normal for firmware upload
        return False

if __name__ == '__main__':
    upload_firmware()
