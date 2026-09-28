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

Segment Breivika to Longyearbyen, 1,375 km with 20 repeaters. **Assumption:** repeaters evenly spaced (about 65.5 km); the real span plan is not public.

| Case | Heard | Longest deaf stretch |
|---|---|---|
| Interrogator at one landing | 65.5 km (4.8 %) | 1,310 km |
| Interrogators at both landings | 130.9 km (9.5 %) | 1,244 km |
| Both landings, 200.6 km reach (enhanced-scattering fibre) | 130.9 km (9.5 %) | 1,244 km |
| Both landings, multi-span repeaters (HLLB) | 1,375 km (100 %) | 0 km |

Depth along the approximate public route (GEBCO 2020 via OpenTopoData, positions scaled to 1,375 km): of the stretch deeper than 1,000 m, about 94 % lies in the deaf part.

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

MIT licence.
