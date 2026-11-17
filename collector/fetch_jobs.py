import csv, json, re, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config/settings.json").read_text(encoding="utf-8"))
FIELDS = ["id","title","company","location","published","source","url","description","collected_at"]

def clean(s):
    return re.sub(r"\\s+", " ", re.sub(r"<[^>]+>", " ", unescape(s or ""))).strip()

def date_value(s):
    try:
        d = parsedate_to_datetime(s)
        if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc).isoformat()
    except Exception: return s or ""

def fetch(src):
    req = urllib.request.Request(src["url"], headers={"User-Agent":"AI-Freelance-Job-Hunter/1.0"})
    with urllib.request.urlopen(req, timeout=CFG.get("request_timeout_seconds",25)) as r: root = ET.fromstring(r.read())
    channel = root.find("channel")
    items = channel.findall("item") if channel is not None else root.findall(".//{*}entry")
    now, out = datetime.now(timezone.utc).isoformat(), []
    for item in items:
        def val(tag):
            n = item.find(tag)
            if n is None: n = item.find("{*}"+tag)
            return n.text if n is not None and n.text else ""
        link = val("link")
        if not link:
            n = item.find("{*}link")
            link = n.attrib.get("href","") if n is not None else ""
        title = clean(val("title"))
        if not title or not link: continue
        guid = val("guid") or val("id") or link
        out.append({"id":re.sub(r"[^a-zA-Z0-9_-]+","-",guid)[:150],"title":title,"company":"","location":"","published":date_value(val("pubDate") or val("published") or val("updated")),"source":src["name"],"url":link.strip(),"description":clean(val("description") or val("summary") or val("content"))[:4000],"collected_at":now})
    return out

def main():
    jobs, errors = [], []
    for src in CFG["sources"]:
        try:
            found = fetch(src); jobs.extend(found); print(src["name"],len(found))
        except Exception as e:
            errors.append(src["name"]+": "+str(e)); print("WARNING:",errors[-1])
    unique, seen = [], set()
    for j in jobs:
        key = j["url"].split("?")[0].rstrip("/").lower()
        if key and key not in seen: seen.add(key); unique.append(j)
    unique.sort(key=lambda x:x["published"], reverse=True)
    unique = unique[:int(CFG.get("max_jobs",500))]
    data = {"updated_at":datetime.now(timezone.utc).isoformat(),"count":len(unique),"errors":errors,"jobs":unique}
    (ROOT/"data").mkdir(exist_ok=True)
    (ROOT/"data/jobs.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    with (ROOT/"data/jobs.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(unique)
    print("Saved",len(unique),"unique jobs")

if __name__ == "__main__": main()
