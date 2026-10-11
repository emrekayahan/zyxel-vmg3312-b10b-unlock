import urllib.request
import re

url = "https://www.wch.cn/downloads/CH341SER_EXE.html"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        content = r.read().decode("utf-8", errors="ignore")
        for m in re.finditer(r'(https?://[^\s"\'<>]+)', content):
            link = m.group(1)
            if any(ext in link.lower() for ext in [".exe", ".zip", "down", "file"]):
                print("Link:", link)
except Exception as e:
    print("Hata:", e)
