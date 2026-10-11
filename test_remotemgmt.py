import urllib.request
import urllib.parse
import re
import http.cookiejar

cj = http.cookiejar.MozillaCookieJar('cookie.txt')
cj.load()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# fetch remoteMGMT.html
resp = opener.open('http://192.168.1.3/pages/maintenance/remoteMGMT/remoteMGMT.html')
html = resp.read().decode('utf-8', errors='ignore')
sk = re.search(r'sessionKey["\'][^>]*value=["\'](\d+)["\']', html, re.IGNORECASE)
if not sk:
    sk = re.search(r'value=["\'](\d+)["\'][^>]*sessionKey', html, re.IGNORECASE)
print('Found sessionKey:', sk.group(1) if sk else None)
if sk:
    session_key = sk.group(1)
    data = {
        'sessionKey': session_key,
        'httpsLan': '2',
        'httpsPort': '443',
        'httpLan': '2',
        'httpPort': '80',
        'telnetLan': '2',
        'telnetPort': '23',
        'ftpLan': '2',
        'ftpPort': '21',
        'icmpLan': '2'
    }
    req = urllib.request.Request(
        'http://192.168.1.3/pages/tabFW/remoteMGMT-remoteMGMT.cgi',
        data=urllib.parse.urlencode(data).encode('utf-8'),
        headers={'Referer': 'http://192.168.1.3/pages/maintenance/remoteMGMT/remoteMGMT.html'}
    )
    res = opener.open(req)
    print('Response code:', res.status)
    print('Response headers:', res.headers.items())
    body = res.read().decode('utf-8', errors='ignore')
    print('Response body preview:', body[:300])
