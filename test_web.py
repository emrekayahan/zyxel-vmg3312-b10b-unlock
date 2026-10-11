import urllib.request
import urllib.parse
import http.cookiejar
import re

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Login
login_data = urllib.parse.urlencode({'AuthName': 'admin', 'AuthPassword': 'turktelekom'}).encode()
req = urllib.request.Request('http://192.168.1.1/login/login-page.cgi', data=login_data)
try:
    resp = opener.open(req)
    html = resp.read().decode('latin1', errors='replace')
    print("Login OK. Cookies:", [f"{c.name}={c.value}" for c in cj])
    
    # Check if skip button exists
    forms = re.findall(r'<form[^>]*action=[\'"]([^\'"]+)[\'"][^>]*>(.*?)</form>', html, re.DOTALL | re.I)
    print(f"Found {len(forms)} forms on landing page:")
    for action, fbody in forms:
        inputs = re.findall(r'<input[^>]*name=[\'"]([^\'"]+)[\'"][^>]*value=[\'"]([^\'"]*)[\'"]', fbody, re.I)
        print(f"  Form action: {action}, inputs: {inputs}")

    # Check firmware upgrade page directly
    fw_url = 'http://192.168.1.1/pages/maintenance/firmwareUpgrade/firmwareUpgrade.html'
    try:
        fw_resp = opener.open(fw_url)
        fw_html = fw_resp.read().decode('latin1', errors='replace')
        print(f"Firmware Upgrade page: {len(fw_html)} bytes")
        if 'firmware' in fw_html.lower():
            print("  [+] Firmware upgrade page content is accessible!")
            for line in fw_html.splitlines()[:20]:
                if line.strip():
                    print("   ", line.strip()[:80])
    except Exception as e:
        print("Firmware Upgrade page error:", e)

    # Logout to free session
    try:
        opener.open('http://192.168.1.1/login/logout.cgi')
        print("Logged out cleanly.")
    except:
        pass

except Exception as e:
    print("Error:", e)
