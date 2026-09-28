"""Coverage model for distributed acoustic sensing (DAS) on a repeatered subsea segment.

Physics that sets the model:
  * A DAS interrogator reads Rayleigh backscatter from its own end of the fibre.
  * Ordinary optical repeaters are one-way: backscatter from beyond the first repeater never
    returns (Xenaki et al., arXiv:2502.18344, Sec. B).
  * Within the first span, the optical budget limits range (commercial units ~171 km).
  * Repeaters with high-loss loopback (HLLB) paths, or bidirectional repeaters, let DAS
    continue span by span (multi-span DAS); not commercially available as of 2025.
  * State-of-polarisation (SOP) sensing on live traffic integrates over the whole length
    but does not localise along it (Landro et al., Sci. Rep. 2022).
Everything is a bound on *where* the fibre can listen, not on what it will detect there.
"""
from dataclasses import dataclass


@dataclass
class Segment:
    length_km: float
    repeaters: int = 0                 # evenly spaced unless spans_km is given
    spans_km: tuple = None             # explicit span lengths, shore to shore
    reach_km: float = 171.0            # optical reach of the interrogator in one span
    dual_ended: bool = False           # an interrogator at both landings
    multispan: bool = False            # HLLB / bidirectional repeaters available
    max_spans: int = None              # multi-span limit per end (None = unlimited)

    def spans(self):
        if self.spans_km:
            s = list(self.spans_km)
            if abs(sum(s) - self.length_km) > 1e-6:
                raise ValueError("spans_km must add up to length_km")
            return s
        n = self.repeaters + 1
        return [self.length_km / n] * n


def _merge(iv):
    iv = sorted((a, b) for a, b in iv if b > a)
    out = []
    for a, b in iv:
        if out and a <= out[-1][1] + 1e-9:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def _from_end(spans, reach, multispan, max_spans):
    """Intervals heard from the start of `spans` (km measured from that end)."""
    heard, x = [], 0.0
    for i, s in enumerate(spans):
        if i > 0 and not multispan:
            break
        if max_spans is not None and i >= max_spans:
            break
        heard.append((x, x + min(s, reach)))
        if reach < s:          # optical budget exhausted inside this span
            break
        x += s
    return heard


def heard_intervals(seg: Segment):
    sp = seg.spans()
    L = seg.length_km
    iv = _from_end(sp, seg.reach_km, seg.multispan, seg.max_spans)
    if seg.dual_ended:
        iv += [(L - b, L - a) for a, b in _from_end(sp[::-1], seg.reach_km, seg.multispan, seg.max_spans)]
    return _merge(iv)


def coverage(seg: Segment):
    iv = heard_intervals(seg)
    L = seg.length_km
    heard = sum(b - a for a, b in iv)
    gaps, x = [], 0.0
    for a, b in iv:
        if a > x:
            gaps.append((x, a))
        x = max(x, b)
    if x < L:
        gaps.append((x, L))
    longest = max((b - a for a, b in gaps), default=0.0)
    return {"length_km": L, "span_km": [round(s, 2) for s in seg.spans()], "heard_km": round(heard, 2),
            "fraction": heard / L if L else 0.0, "heard": [(round(a, 2), round(b, 2)) for a, b in iv],
            "deaf": [(round(a, 2), round(b, 2)) for a, b in gaps], "longest_deaf_km": round(longest, 2)}


def sweep(length_km, spacings_km, reaches_km, dual_ended=True):
    """Coverage fraction for evenly spaced repeaters across spacing x reach."""
    rows = []
    for s in spacings_km:
        n = max(0, round(length_km / s) - 1)
        for r in reaches_km:
            c = coverage(Segment(length_km, repeaters=n, reach_km=r, dual_ended=dual_ended))
            rows.append({"spacing_km": s, "repeaters": n, "reach_km": r, "fraction": round(c["fraction"], 4),
                         "longest_deaf_km": c["longest_deaf_km"]})
    return rows


def apply_profile(seg: Segment, samples, route_km, depth_limit_m=-1000.0):
    """Map heard/deaf intervals onto a depth profile sampled along an approximate route.

    samples: list of {"km_route": x, "elev_m": z} along a route of length route_km (map line).
    Positions are scaled linearly to the segment's official length.
    Returns deep (below depth_limit_m) kilometres that are heard vs deaf.
    """
    k = seg.length_km / route_km
    iv = heard_intervals(seg)
    pts = [(s["km_route"] * k, s["elev_m"]) for s in samples]
    deep_heard = deep_deaf = 0.0
    for (x0, z0), (x1, _) in zip(pts, pts[1:]):
        if z0 > depth_limit_m:
            continue
        mid = (x0 + x1) / 2
        if any(a <= mid <= b for a, b in iv):
            deep_heard += x1 - x0
        else:
            deep_deaf += x1 - x0
    tot = deep_heard + deep_deaf
    return {"depth_limit_m": depth_limit_m, "deep_km": round(tot, 1), "deep_heard_km": round(deep_heard, 1),
            "deep_deaf_km": round(deep_deaf, 1), "deep_deaf_fraction": round(deep_deaf / tot, 4) if tot else 0.0,
            "min_elev_m": min(z for _, z in pts), "scale": round(k, 4)}
