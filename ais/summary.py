"""Summarise the Svalbard crossing counts in data/ais/ (offline; no network).
Usage: python -m ais.summary
Windows are cut at 03:10 UTC on 7 January (the 2022 fault was at 04:10 CET) and to route km 80-280."""
import json, glob, pathlib, collections
H = pathlib.Path(__file__).resolve().parent.parent
MID = {"273":"Russia","257":"Norway","258":"Norway","259":"Norway","231":"Faroe Is.","251":"Iceland","219":"Denmark","220":"Denmark","265":"Sweden","266":"Sweden","230":"Finland","211":"Germany","218":"Germany","232":"UK","233":"UK","235":"UK","244":"Netherlands","245":"Netherlands","246":"Netherlands","209":"Cyprus","210":"Cyprus","212":"Cyprus","215":"Malta","229":"Malta","248":"Malta","249":"Malta","256":"Malta","636":"Liberia","538":"Marshall Is.","351":"Panama","352":"Panama","353":"Panama","354":"Panama","355":"Panama","356":"Panama","357":"Panama","370":"Panama","371":"Panama","372":"Panama","373":"Panama","374":"Panama","224":"Spain","225":"Spain","226":"France","227":"France","228":"France","247":"Italy","261":"Poland","276":"Estonia","275":"Latvia","277":"Lithuania","412":"China","413":"China","414":"China","477":"Hong Kong"}
def flag(m): return MID.get(str(m)[:3], "other")
FAULT_ZONE = (130, 230)   # operator estimate (Space Norway via NUPI Policy Brief 1/2023)

def window(path, year):
    d = json.load(open(path))
    c = [x for x in d["crossings"] if x["time"] < f"{year}-01-07T03:10:00" and 80 <= x["km"] <= 280]
    return {"winter": f"{year-1}/{str(year)[2:]}", "failed_queries": len(d["failed"]), "crossings": len(c),
            "russian": sum(flag(x["mmsi"]) == "Russia" for x in c),
            "in_fault_zone": sum(FAULT_ZONE[0] <= x["km"] <= FAULT_ZONE[1] for x in c),
            "vessels": len({x["mmsi"] for x in c})}

def baseline_2025(span_km=1375/21, L=1375):
    X, days, failed = [], set(), 0
    for f in sorted(glob.glob(str(H/"data/ais/ais_crossings_y2025_w*.json"))):
        d = json.load(open(f)); X += d["crossings"]; days |= set(d["days"]); failed += len(d["failed"])
    near = sum(1 for x in X if x["km"] <= span_km or x["km"] >= L - span_km)
    return {"days": len(days), "failed_queries": failed, "crossings": len(X), "vessels": len({x["mmsi"] for x in X}),
            "russian": sum(flag(x["mmsi"]) == "Russia" for x in X), "within_first_span_either_end": near}

if __name__ == "__main__":
    rows = [window(H/"data/ais/ais_crossings_jan2022.json", 2022)] + \
           [window(f, int(pathlib.Path(f).stem[-4:])) for f in sorted(glob.glob(str(H/"data/ais/ais_crossings_win*.json")))]
    print(f"{'winter':<10}{'crossings':>10}{'russian':>9}{'fault zone':>12}{'vessels':>9}")
    for r in rows: print(f"{r['winter']:<10}{r['crossings']:>10}{r['russian']:>9}{r['in_fault_zone']:>12}{r['vessels']:>9}")
    print("2025 baseline:", baseline_2025())
