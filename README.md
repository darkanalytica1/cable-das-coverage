# cable-das-coverage

**Which kilometres of a repeatered subsea cable can a DAS interrogator actually hear?**

A small, dependency-free calculator. Give it a cable segment (length, repeaters, interrogator reach, one or both landings, multi-span repeaters or not) and it returns the stretches that can be interrogated, the fraction of the cable they cover and the longest deaf stretch. An optional depth profile tells you how much of the deep water falls in the deaf part.

## Why it matters

Distributed acoustic sensing turns a telecom fibre into thousands of microphones. On a Svalbard cable it has detected whales, ships, storms and earthquakes over about 120 km of fibre (Landrø et al., 2022). That makes every cable a candidate sensor for its own protection.

The limit is optical, not acoustic. Ordinary repeaters are one-way gates for the backscattered light DAS depends on, so an interrogator on land hears only as far as the first repeater (Xenaki et al., 2025). On long repeatered cables that is a small fraction of the route, and it is the shallow fraction near the coast.

## Quick start (verified)

```bash
python -m dascov          # Svalbard example and a spacing x reach sweep
python -m dascov --json   # same results as JSON
python -m unittest discover -s tests
```

```python
from dascov import Segment, coverage
coverage(Segment(1375, repeaters=20, reach_km=171, dual_ended=True))["fraction"]   # 0.095
```

## Svalbard example (results)

Segment Breivika to Longyearbyen, 1,375 km with 20 repeaters. **Assumption:** repeaters evenly spaced (about 65.5 km); the real span plan is not public, and the operator has described the spacing as roughly 100 km, so both cases are shown.

| Case | Heard | Longest deaf stretch |
|---|---|---|
| Interrogator at one landing | 65.5 km (4.8 %) | 1,310 km |
| Interrogators at both landings | 130.9 km (9.5 %) | 1,244 km |
| Both landings, 200.6 km reach (enhanced-scattering fibre) | 130.9 km (9.5 %) | 1,244 km |
| Both landings, multi-span repeaters (HLLB) | 1,375 km (100 %) | 0 km |
| Both landings, first spans of 100 km (operator's "approximately 100 km") | 200 km (14.5 %) | 1,175 km |

Depth along the approximate public route (GEBCO 2020 via OpenTopoData, positions scaled to 1,375 km): of the stretch deeper than 1,000 m, about 94 % lies in the deaf part.

## Svalbard: who crosses the route (open AIS)

`ais/` counts how often vessel tracks cross the approximate Svalbard route, from the Norwegian Coastal Administration's open AIS (Kystdatahuset API, NLOD licence). The 2022 fault was estimated by the operator at 130 to 230 km from Longyearbyen, beyond the first repeater under either spacing.

```bash
python -m ais.summary                     # offline, from the query outputs in data/ais/
python ais/crossings.py jan2022           # re-query 25.12.2021-07.01.2022 (network, slow)
python ais/crossings.py win 2024          # same window in a later winter
python ais/crossings.py y2025 0 4         # 2025 fortnightly baseline, worker 0 of 4
```

Same 13 days (25 December to 7 January 03:10 UTC), route km 80 to 280:

| Winter | Crossings | Russian-flagged | In fault zone (km 130-230) | Vessels |
|---|---|---|---|---|
| 2021/22 (fault) | 281 | 231 | 96 | 33 |
| 2022/23 | 273 | 255 | 61 | 15 |
| 2023/24 | 62 | 35 | 12 | 5 |
| 2024/25 | 73 | 63 | 8 | 6 |
| 2025/26 | 6 | 0 | 2 | 2 |

2025 baseline (26 days, one every 14 days, full route): 758 crossings by 296 vessels, 65 Russian-flagged; 601 within one 65.5 km span of either landing.

Method: per UTC day and route piece, positions at 0.3 kn or more in a box around the piece; consecutive fixes under 30 minutes apart joined and tested for intersection with the route line. Flag from the MMSI country code. Counts are lower bounds: AIS excludes fishing vessels under 15 m and anything not transmitting, and gaps over 30 minutes are not bridged. The route is approximate and the real system is two cables 5 to 10 km apart, so these are crossings of a corridor, not of a cable. **A crossing is not evidence of damage.** The fall after 2022/23 is observed, not explained.

`data/incidents.csv` lists the Arctic and Baltic subsea incidents used for context, with sources.

## Limitations

- Coverage is where the fibre *can* listen, not what it will detect: detection depends on source level, frequency, coupling, burial, noise and processing.
- Even repeater spacing is assumed unless you pass `spans_km`.
- Multi-span DAS is modelled as full coverage per span; real systems lose SNR span by span and none were commercially available as of 2025.
- The route and depth profile come from a public map line, which is approximate.
- Polarisation (SOP) sensing on live traffic covers the whole length but is not modelled: it does not localise along the cable.

## Sources

- Landrø, M. et al. (2022). Sensing whales, storms, ships and earthquakes using an Arctic fibre optic cable. *Scientific Reports* 12, 19226.
- Xenaki, A., Gerstoft, P., Williams, E., Abadi, S. (2025). Overview of distributed acoustic sensing: theory and ocean applications. arXiv:2502.18344.
- Zhu, B. et al. (2025). Integration of distributed acoustic sensing and unrepeatered transmission for undersea cable monitoring by ESF. SubOptic 2025.
- Svalbard Undersea Cable System (segment lengths, repeaters), Wikipedia.
- GEBCO Compilation Group (2020), via api.opentopodata.org.
- Norwegian Coastal Administration, open AIS data (NLOD), kystdatahuset.no.
- Schia, N. N., Gjesvik, L., Rødningen, I. F. (2023). The subsea cable cut at Svalbard January 2022. NUPI Policy Brief 1/2023.
- Space Norway (2022). Redundancy on primary telecom connection to Svalbard restored.

MIT licence.
