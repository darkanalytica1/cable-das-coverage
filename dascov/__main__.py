"""python -m dascov            -> Svalbard example + sweep (text)
   python -m dascov --json     -> same, as JSON"""
import json, sys, os
from .coverage import Segment, coverage, sweep, apply_profile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def svalbard():
    # Svalbard Undersea Cable System, segment Breivika - Longyearbyen: 1,375 km, 20 repeaters
    # (Wikipedia). Even spacing is an ASSUMPTION: the real span plan is not public.
    L, n = 1375.0, 20
    cases = {
        "single_ended": Segment(L, n, reach_km=171, dual_ended=False),
        "dual_ended": Segment(L, n, reach_km=171, dual_ended=True),
        "dual_ended_enhanced_scattering_200km": Segment(L, n, reach_km=200.6, dual_ended=True),
        "multispan_hllb_both_ends": Segment(L, n, reach_km=171, dual_ended=True, multispan=True),
    }
    res = {k: coverage(v) for k, v in cases.items()}
    prof = json.load(open(os.path.join(HERE, "data", "svalbard_profile_gebco.json")))
    res["deep_water"] = {d: apply_profile(cases["dual_ended"], prof["samples"], prof["route_km"], d)
                         for d in (-1000.0, -2000.0)}
    res["second_segment_1339km_dual"] = coverage(Segment(1339.0, 20, reach_km=171, dual_ended=True))
    res["sweep_1375km_dual"] = sweep(L, [40, 50, 65, 80, 100], [50, 100, 171])
    return res


def main(argv):
    r = svalbard()
    if "--json" in argv:
        print(json.dumps(r, indent=1)); return
    for k in ("single_ended", "dual_ended", "dual_ended_enhanced_scattering_200km", "multispan_hllb_both_ends",
              "second_segment_1339km_dual"):
        c = r[k]
        print(f"{k:40s} heard {c['heard_km']:7.1f} km of {c['length_km']:.0f} "
              f"({100*c['fraction']:5.1f} %), longest deaf stretch {c['longest_deaf_km']:.0f} km")
    for d, p in r["deep_water"].items():
        print(f"deeper than {-float(d):.0f} m: {p['deep_km']} km, deaf {p['deep_deaf_km']} km "
              f"({100*p['deep_deaf_fraction']:.1f} %), GEBCO min {p['min_elev_m']} m on the map route")
    print("sweep (1,375 km, dual-ended): spacing x reach -> fraction heard")
    for row in r["sweep_1375km_dual"]:
        print(f"  {row['spacing_km']:4d} km  {row['reach_km']:4d} km  {100*row['fraction']:5.1f} %")


if __name__ == "__main__":
    main(sys.argv[1:])
