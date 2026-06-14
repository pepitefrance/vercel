from http.server import BaseHTTPRequestHandler
import json, urllib.request, urllib.parse, http.cookiejar

VINTED_FR = "https://www.vinted.fr"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer": "https://www.vinted.fr/",
}

def get_session():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    try:
        opener.open(urllib.request.Request(VINTED_FR, headers={"User-Agent": HEADERS["User-Agent"], "Accept": "text/html"}), timeout=8)
        return {c.name: c.value for c in cj}, opener
    except:
        return {}, None

def search(query, per_page=20):
    cookies, opener = get_session()
    if not opener:
        return []
    params = urllib.parse.urlencode({"search_text": query, "per_page": per_page, "order": "newest_first", "currency": "EUR"})
    url = f"{VINTED_FR}/api/v2/catalog/items?{params}"
    req = urllib.request.Request(url, headers={**HEADERS, "Cookie": "; ".join(f"{k}={v}" for k, v in cookies.items())})
    try:
        with opener.open(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except:
        return []
    results = []
    for item in data.get("items", []):
        try:
            photos = item.get("photos", [])
            photo = photos[0].get("url", "") if photos else ""
            results.append({
                "id": f"vinted_{item.get('id','')}",
                "name": item.get("title","Article vintage"),
                "price": float(item.get("price",0)),
                "image": photo,
                "url": f"{VINTED_FR}/items/{item.get('id','')}",
                "src": "vinted",
                "cat": "mode",
                "loc": item.get("user",{}).get("city","France"),
                "caption": item.get("title","")[:40],
                "tags": [item.get("brand_title","Vintage")],
                "rot": 0,
                "bg": "#E8F5E8",
            })
        except:
            continue
    return results

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        q = p.get("q", ["vintage brocante"])[0]
        items = search(q, int(p.get("limit", [20])[0]))
        body = json.dumps({"source":"vinted","count":len(items),"items":items}, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "max-age=120")
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a): pass
