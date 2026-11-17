import csv, json, re, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "config/settings.json").read_text(encoding="utf-8"))
FIELDS = ["id","title","company","location","published","source","url","apply_url","description","salary","employment_type","eligibility","fit_score","difficulty","android_feasibility","reasons","verification_status","risk_level","risk_flags","collected_at"]

def clean(s):
    return re.sub(r"\\s+", " ", re.sub(r"<[^>]+>", " ", unescape(str(s or "")))).strip()

def date_value(s):
    try:
        if isinstance(s, (int, float)):
            return datetime.fromtimestamp(s, timezone.utc).isoformat()
        d = parsedate_to_datetime(str(s))
        if d.tzinfo is None: d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc).isoformat()
    except Exception: return str(s or "")

def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent":"AI-Freelance-Job-Hunter/1.1","Accept":"application/json"})
    with urllib.request.urlopen(req, timeout=CFG.get("request_timeout_seconds",25)) as r:
        return json.loads(r.read().decode("utf-8"))

def fetch_rss(src):
    req = urllib.request.Request(src["url"], headers={"User-Agent":"AI-Freelance-Job-Hunter/1.1"})
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
        out.append({"id":re.sub(r"[^a-zA-Z0-9_-]+","-",guid)[:150],"title":title,"company":"","location":"","published":date_value(val("pubDate") or val("published") or val("updated")),"source":src["name"],"url":link.strip(),"description":clean(val("description") or val("summary") or val("content"))[:5000],"salary":"","employment_type":"","eligibility":"Belum diketahui — periksa negara yang diterima di halaman asli","collected_at":now})
    return out

def fetch_himalayas(src):
    out, cursor = [], None
    for _ in range(int(src.get("pages",3))):
        params={"limit":20}
        if cursor: params["cursor"]=cursor
        data=get_json(src["url"]+"?"+urlencode(params))
        jobs=data.get("jobs", data.get("data", []))
        if isinstance(jobs, dict): jobs=jobs.get("jobs", [])
        for j in jobs:
            restrictions=j.get("locationRestrictions") or []
            zones=j.get("timezoneRestrictions") or []
            if restrictions and not any(str(x).lower() in ("id","indonesia") for x in restrictions):
                eligibility="Tidak menerima Indonesia menurut batas negara yang tercantum"
            elif zones and not any(str(x).replace("UTC","").strip() in ("7","+7","+07:00","7:00") for x in zones):
                eligibility="Zona waktu perlu diperiksa; Indonesia UTC+7"
            elif restrictions:
                eligibility="Indonesia tercantum sebagai lokasi yang diterima"
            else:
                eligibility="Terbuka menurut batas negara; cek zona waktu dan halaman asli"
            salary=""
            if j.get("minSalary") or j.get("maxSalary"):
                salary=f'{j.get("minSalary") or ""}-{j.get("maxSalary") or ""} {j.get("currency") or ""} / {j.get("salaryPeriod") or "annual"}'
            out.append({"id":str(j.get("guid") or j.get("id") or j.get("applicationLink") or j.get("title")),"title":clean(j.get("title")),"company":clean(j.get("companyName")),"location":clean(", ".join(restrictions) if restrictions else "Remote; country unrestricted"),"published":date_value(j.get("pubDate")),"source":src["name"],"url":((str(j.get("guid","")) if str(j.get("guid","")).startswith("http") else "https://himalayas.app/"+str(j.get("guid","")).lstrip("/")) if j.get("guid") else (j.get("url") or "https://himalayas.app/jobs")),"apply_url":j.get("applicationLink") or "","description":clean(j.get("description") or j.get("excerpt"))[:5000],"salary":salary,"employment_type":clean(j.get("employmentType")),"eligibility":eligibility,"collected_at":datetime.now(timezone.utc).isoformat()})
        cursor=data.get("nextCursor")
        if not cursor or not jobs: break
    return out

def assess(job):
    text=(job.get("title","")+" "+job.get("description","")).lower()
    score=35; reasons=[]
    positive={"virtual assistant":18,"assistant":10,"data entry":18,"customer support":16,"customer service":14,"chat support":18,"content writer":15,"copywriter":12,"social media":15,"community moderator":15,"moderator":12,"transcription":18,"translator":12,"research assistant":14,"junior":15,"entry level":20,"entry-level":20,"intern":18,"trainee":15,"part-time":5}
    negative={"senior":-25,"staff engineer":-30,"director":-30,"head of":-25,"principal":-25,"lead engineer":-20,"5+ years":-25,"7+ years":-30,"10+ years":-30,"3+ years":-12,"phd":-15,"doctor":-25,"physician":-30}
    for k,v in positive.items():
        if k in text: score+=v; reasons.append("Cocok: "+k)
    for k,v in negative.items():
        if k in text: score+=v; reasons.append("Hambatan: "+k)
    elig=job.get("eligibility","")
    if "Tidak menerima Indonesia" in elig: score-=45; reasons.append("Lokasi tidak cocok untuk Indonesia")
    elif "Indonesia tercantum" in elig: score+=15; reasons.append("Indonesia tercantum sebagai lokasi yang diterima")
    if any(x in text for x in ["worldwide","work from anywhere","anywhere in the world"]): score+=8; reasons.append("Menyebut worldwide")
    if any(x in text for x in ["must be based in","only applicants","residents of","united states only","us only","canada only","uk only"]): score-=20; reasons.append("Ada pembatasan negara yang perlu dicek")
    if any(x in text for x in ["windows","excel","google sheets","email","calendar","research","document","canva","social media"]): score+=5
    if any(x in text for x in ["computer required","desktop computer","laptop required","high-end pc","workstation"]):
        android="Tidak cocok — mensyaratkan komputer"
    elif any(x in text for x in ["fast reliable internet","video calls","multiple systems","software","spreadsheet","clickup","crm"]):
        android="Meragukan — kemungkinan perlu laptop"
    else:
        android="Belum diketahui — cek perangkat kerja"
    score=max(0,min(100,score))
    difficulty="Mudah-menengah" if score>=65 else ("Menengah" if score>=45 else "Sulit / kurang cocok")
    if "Tidak menerima Indonesia" in elig: difficulty="Tidak cocok lokasi"
    return score,difficulty,android,reasons[:8]

def assess_risk(job):
    """
    Heuristic warning only. It cannot prove a job is legitimate or fraudulent.
    """
    text = (job.get("title", "") + " " + job.get("description", "")).lower()
    checks = [
        ("Meminta biaya untuk melamar atau diterima", r"\b(pay|send|transfer)\b.{0,50}\b(application|registration|training|processing|recruitment) fee\b|\b(application|registration|training|processing) fee\b.{0,50}\b(required|must pay|pay)\b"),
        ("Meminta pembayaran deposit atau uang jaminan", r"\b(deposit|security fee|upfront payment)\b"),
        ("Meminta kata sandi atau OTP", r"\b(password|one.time password|\botp\b|verification code)\b.{0,50}\b(send|share|provide|tell us)\b|\b(send|share|provide|tell us)\b.{0,50}\b(password|\botp\b|verification code)\b"),
        ("Meminta transfer atau pembayaran dengan kripto", r"\b(pay|payment|transfer)\b.{0,50}\b(bitcoin|crypto|cryptocurrency|gift card)\b|\b(bitcoin|crypto|cryptocurrency|gift card)\b.{0,50}\b(pay|payment|transfer)\b"),
    ]
    flags = [label for label, pattern in checks if re.search(pattern, text)]
    return {
        "verification_status": "Perlu verifikasi manual",
        "risk_level": "Perlu perhatian" if flags else "Tidak ada tanda otomatis yang terdeteksi",
        "risk_flags": flags
    }

def main():
    jobs, errors = [], []
    for src in CFG["sources"]:
        try:
            found=fetch_himalayas(src) if src.get("type")=="himalayas" else fetch_rss(src)
            jobs.extend(found); print(src["name"],len(found))
        except Exception as e:
            errors.append(src["name"]+": "+str(e)); print("WARNING:",errors[-1])
    unique, seen = [], set()
    for j in jobs:
        key=j.get("url","").split("?")[0].rstrip("/").lower()
        if key and key not in seen:
            seen.add(key)
            score,difficulty,android,reasons=assess(j)
            j.update({"fit_score":score,"difficulty":difficulty,"android_feasibility":android,"reasons":reasons,**assess_risk(j)})
            unique.append(j)
    unique.sort(key=lambda x:(x["fit_score"],x["published"]),reverse=True)
    unique=unique[:int(CFG.get("max_jobs",500))]
    data={"updated_at":datetime.now(timezone.utc).isoformat(),"count":len(unique),"errors":errors,"jobs":unique}
    (ROOT/"data").mkdir(exist_ok=True)
    (ROOT/"data/jobs.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    with (ROOT/"data/jobs.csv").open("w",newline="",encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS); w.writeheader(); w.writerows(unique)
    print("Saved",len(unique),"unique jobs; high-fit:",sum(1 for j in unique if j["fit_score"]>=65))

if __name__=="__main__": main()
