import urllib.request
import http.cookiejar
import re

cj = http.cookiejar.MozillaCookieJar('cookie.txt')
try:
    cj.load()
except:
    pass
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# First check if we can reach firmwareUpgrade.html
try:
    req = urllib.request.Request('http://192.168.1.3/pages/maintenance/firmwareUpgrade/firmwareUpgrade.html')
    resp = opener.open(req)
    html = resp.read().decode('utf-8', errors='ignore')
    
    # check for error message or idxStr
    m_idx = re.search(r'idxStr\s*=\s*[\'"](\d+)[\'"]', html)
    print("idxStr:", m_idx.group(1) if m_idx else "None")
    
    m_ver = re.search(r'Mevcut Ayg.*?Yaz.*?S.*?r.*?m.*?font[^>]*>(.*?)</font>', html, re.DOTALL)
    print("Current Firmware:", m_ver.group(1).strip() if m_ver else "Unknown")
    
    # print all var declarations
    vars_found = re.findall(r'var\s+([A-Za-z0-9_]+)\s*=\s*[\'"](.*?)[\'"]', html)
    for k, v in vars_found[:15]:
        print(f"  {k} = {v}")
except Exception as e:
    print("Error:", e)
