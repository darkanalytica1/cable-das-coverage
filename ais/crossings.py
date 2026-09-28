"""Count vessel crossings of the (approximate) Svalbard cable route from Kystverket open AIS (Kystdatahuset, NLOD).
Method: route polyline -> ~50 km pieces; per day per piece, query AIS positions in a bbox around the piece
(minSpeed 0.3 kn to drop moored); per vessel, sort positions by time and test each consecutive segment for
intersection with the route line (local equirectangular km). Output one row per crossing.
Limits: route is the approximate public line (7 vertices) scaled to 1,375 km; AIS excludes fishing vessels <15 m and
vessels not transmitting; gaps > 30 min between fixes are not interpolated (crossing not counted)."""
import json, math, sys, time, gzip, pathlib, datetime as dt, urllib.request
H = pathlib.Path(__file__).resolve().parent.parent
R = json.load(open(H / "data/svalbard_route.json"))
URL = "https://kystdatahuset.no/ws/api/ais/positions/within-bbox-time"
LAT0 = 74.0
def xy(lon, lat): return ((lon) * 111.32 * math.cos(math.radians(LAT0)), lat * 110.57)
route = R["route"]; cum = R["cum_km"]; scale = R["scale"]
def pt(km_geo):
    i = 1
    while i < len(cum) - 1 and cum[i] < km_geo: i += 1
    t = max(0, min(1, (km_geo - cum[i-1]) / (cum[i] - cum[i-1])))
    return [route[i-1][0] + t*(route[i][0]-route[i-1][0]), route[i-1][1] + t*(route[i][1]-route[i-1][1])]
G = cum[-1]; N = 28
pieces = []
for k in range(N):
    a, b = G*k/N, G*(k+1)/N
    pts = [pt(a + (b-a)*j/10) for j in range(11)]
    lons = [p[0] for p in pts]; lats = [p[1] for p in pts]
    pieces.append({"k": k, "km_real": [a*scale, b*scale], "pts": pts,
                   "bbox": f"{min(lons)-0.35:.3f},{min(lats)-0.08:.3f},{max(lons)+0.35:.3f},{max(lats)+0.08:.3f}"})
def seg_intersect(p1, p2, q1, q2):
    def cr(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    d1, d2, d3, d4 = cr(q1,q2,p1), cr(q1,q2,p2), cr(p1,p2,q1), cr(p1,p2,q2)
    if (d1*d2 < 0) and (d3*d4 < 0):
        t = d1/(d1-d2); return (p1[0]+t*(p2[0]-p1[0]), p1[1]+t*(p2[1]-p1[1]))
    return None
def fetch(bbox, day):
    body = json.dumps({"bbox": bbox, "start": day.strftime("%Y%m%d0000"), "end": day.strftime("%Y%m%d2359"), "minSpeed": 0.3}).encode()
    for att in range(4):
        try:
            req = urllib.request.Request(URL, body, {"Content-Type": "application/json", "User-Agent": "research/1.0"})
            return json.load(urllib.request.urlopen(req, timeout=180))["data"]
        except Exception as e:
            time.sleep(5*(att+1))
    return None
def crossings(rows, piece):
    out = []; by = {}
    for r in rows: by.setdefault(r[0], []).append(r)
    rl = [xy(*p) for p in piece["pts"]]
    for mmsi, tr in by.items():
        tr.sort(key=lambda r: r[1])
        for a, b in zip(tr, tr[1:]):
            ta = dt.datetime.fromisoformat(a[1]); tb = dt.datetime.fromisoformat(b[1])
            if (tb-ta).total_seconds() > 1800: continue
            pa, pb = xy(a[2], a[3]), xy(b[2], b[3])
            for j in range(len(rl)-1):
                x = seg_intersect(pa, pb, rl[j], rl[j+1])
                if x:
                    frac = (j + (math.dist(rl[j], x)/max(1e-9, math.dist(rl[j], rl[j+1]))))/(len(rl)-1)
                    km = piece["km_real"][0] + frac*(piece["km_real"][1]-piece["km_real"][0])
                    out.append({"mmsi": mmsi, "time": a[1], "km": round(km, 1), "sog": round((a[5]+b[5])/2, 1)})
    return out
if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "jan2022":
        days = [dt.date(2021,12,25) + dt.timedelta(d) for d in range(14)]
        sel = [p for p in pieces if p["km_real"][1] > 80 and p["km_real"][0] < 280]
    elif mode == "win":
        # control: the same 14-day winter window in later years, same route pieces (km 80-280)
        yr = int(sys.argv[2]); mode = f"win{yr}"
        days = [dt.date(yr-1,12,25) + dt.timedelta(d) for d in range(14)]
        sel = [p for p in pieces if p["km_real"][1] > 80 and p["km_real"][0] < 280]
    else:
        alld = [dt.date(2025,1,3) + dt.timedelta(14*i) for i in range(26)]
        w, n = int(sys.argv[2]), int(sys.argv[3])
        days = alld[w::n]; mode = f"{mode}_w{w}"
        sel = pieces
    res = {"mode": mode, "days": [str(d) for d in days], "pieces": [p["km_real"] for p in sel], "crossings": [], "vessels_seen": {}, "failed": []}
    for d in days:
        for p in sel:
            rows = fetch(p["bbox"], d)
            if rows is None: res["failed"].append([str(d), p["k"]]); continue
            for m in set(r[0] for r in rows): res["vessels_seen"][str(m)] = res["vessels_seen"].get(str(m), 0) + 1
            res["crossings"] += crossings(rows, p)
            time.sleep(0.4)
        json.dump(res, open(H / f"data/ais/ais_crossings_{mode}.json", "w"))
        print(d, len(res["crossings"]), flush=True)
