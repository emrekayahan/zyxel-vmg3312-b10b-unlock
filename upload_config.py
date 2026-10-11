import urllib.request
import mimetypes
import http.cookiejar
import sys
import time

MODEM_IP = "192.168.1.3"
USERNAME = "admin"
PASSWORD = "turktelekom1"
CONFIG_FILE = "modified-backupsettings.conf"

def login_and_upload():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    print(f"[*] Modeme oturum aciliyor ({MODEM_IP})...")
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
            print("[-] HATA: Tarayıcınızda veya başka bir cihazda modem arayüzü açık ('A user exist'). Lütfen tarayıcıdaki oturumu kapatıp birkaç dakika bekleyin.")
            return False
        print("[+] Oturum basariyla acildi!")
    except Exception as e:
        print(f"[-] Giris hatasi: {e}")
        return False

    # Read config file
    with open(CONFIG_FILE, 'rb') as f:
        file_bytes = f.read()

    boundary = '----WebKitFormBoundaryX7vT9uK2pL4mQ8wZ'
    body_parts = []
    body_parts.append(f'--{boundary}\r\n'.encode('ascii'))
    body_parts.append(f'Content-Disposition: form-data; name="filename"; filename="{CONFIG_FILE}"\r\n'.encode('ascii'))
    body_parts.append(b'Content-Type: application/octet-stream\r\n\r\n')
    body_parts.append(file_bytes)
    body_parts.append(b'\r\n')
    body_parts.append(f'--{boundary}\r\n'.encode('ascii'))
    body_parts.append(b'Content-Disposition: form-data; name="Upload"\r\n\r\n')
    body_parts.append(b'Upload\r\n')
    body_parts.append(f'--{boundary}--\r\n'.encode('ascii'))

    payload = b''.join(body_parts)

    print(f"[*] {CONFIG_FILE} dosyasi yukleniyor ({len(file_bytes)} bayt)...")
    upload_req = urllib.request.Request(
        f"http://{MODEM_IP}/pages/tabFW/configuration-uploadsettings.cgi",
        data=payload,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Referer": f"http://{MODEM_IP}/pages/maintenance/configuration/configuration.html"
        }
    )

    try:
        up_res = opener.open(upload_req)
        print("[+] Yapilandirma basariyla yuklendi! Modem simdi yeniden baslatiliyor (yaklasik 2-3 dakika surer).")
        return True
    except Exception as e:
        print(f"[-] Yukleme hatasi: {e}")
        return False

if __name__ == '__main__':
    login_and_upload()
