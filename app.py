# app.py
from flask import Flask, jsonify, request
import os, re, math, json
import numpy as np

app = Flask(__name__)

# ============================================================
# Paste/extend the TSV below with ALL 93 ROWS (one per site).
# Columns (tab-separated):
# Region/Site | Status | Estimated RT60 (s) | Dimensions (m, approx. LxWxH) | Sacred Geometry Notes | Simulation Method | Notes/Sources
# ============================================================
DATA_TSV = r"""Region/Site	Status	Estimated RT60 (s)	Dimensions (m, approx. LxWxH)	Sacred Geometry Notes	Simulation Method	Notes/Sources
Egypt / Great Pyramid, King’s Chamber — Giza	Measured (public)	2-3	10.47 x 5.235 x 5.827	Golden ratio (φ) in height:width (≈φ/2), length:width=2:1; base perimeter:height≈2π; resonant freq ~121 Hz (fundamental) or 440 Hz (F# chord). Modes align with harmonic series.	Download public IR; convolve. Synthetic: Shoebox with exact dims, emphasize modes at φ-related freqs.	IR from AudioEase; dims encode pi/phi.
Egypt / Great Pyramid, Queen’s Chamber — Giza	Measured (public)	1-2	5.75 x 5.23 x 6.23	Similar to King’s; sqrt(5) in height; niche ratios follow φ.	Synthetic decay with modes.	Smaller; RT60 ~1.5 s.
Egypt / Great Pyramid, Grand Gallery — Giza	Measured (public)	3-4	46.68 x 2.09 x 8.68	Slope angle ~26° (seked 5.5, related to sqrt(φ)); length:height≈φ^2.	Image-source for corridor; calculate echoes via geometry.	Echo-heavy.
Egypt / Pyramid of Khafre (selected chambers) — Giza	Measured (private/limited)	2-3	~10 x 5 x 6	Pi/phi integrations like Great Pyramid.	Synthetic with φ-scaled dims.	Analogous chambers.
Egypt / Abu Simbel Temple — Aswan	Measured (private/limited)	4-6	18 x 16.4 x 8	Rock-cut with solar alignments; ratios 9:5 (≈φ).	Synthetic hall; mode calc.	Stone resonance.
Egypt / Karnak Temple, Hypostyle Hall — Luxor	Modeled/Simulated	5-8	50 x 103 x 24	Column grid follows 1:√2; vast scale encodes solar ratios.	Shoebox approx.; scatter for columns.	Cathedral-like.
Egypt / Luxor Temple — Luxor	Modeled/Simulated	4-6	190 x 55 x 15 (approx hall)	Avenue aligns with Nile; pylon ratios 4:3 (fifth interval).	Synthetic with open elements.	Reduced RT60.
Egypt / Dendera, Temple of Hathor — Qena	Modeled/Simulated	3-5	10 x 8 x 6	Zodiac ceiling; vesica piscis in layouts.	Synthetic; chapel resonance.	Underground short RT60.
Egypt / Philae Temple — Aswan	Modeled/Simulated	4-6	32 x 18 x 12	Island layout; golden spiral in colonnades.	Synthetic.	Nile influence.
India / Kailasa Temple (Ellora) — Maharashtra	Measured (private/limited)	3-5	60 x 30 x 33 (overall)	Rock-cut mandala; ratios 1:φ:φ^2 (Fibonacci).	Synthetic cave.	Moderate RT60.
India / Konark Sun Temple — Odisha	Modeled/Simulated	4-6	229 x 128 x 20 (base & hall)	Chariot form; 12 wheels (zodiac), ratios 7:4 (solar).	Synthetic with open structure.	Wind-affected.
India / Brihadeeswarar Temple — Tamil Nadu	Modeled/Simulated	5-7	60 x 30 x 30	Height:base≈2:1; shikhara follows sqrt(2).	Synthetic hall.	Long reverb.
India / Meenakshi Temple — Tamil Nadu	Modeled/Simulated	4-6	50 x 30 x 15	Gopuram ratios φ; mandala plan.	Pillared echo.	Like Karnak.
India / Golden Temple (Harmandir Sahib) — Amritsar	Modeled/Simulated	3-5	20 x 20 x 15	Square (stability); dome φ curve.	Short RT60; reflections.	Lake geometry.
India / Jagannath Temple — Puri	Modeled/Simulated	4-6	65 x 20 x 20 (vimana/base)	Vimana ratios 3:2 (fifth).	Synthetic.	Festival acoustics.
India / Kandariya Mahadev (Khajuraho) — Madhya Pradesh	Modeled/Simulated	3-5	31 x 15 x 15	Shikharas in φ progression.	Moderate reverb.	Diffuse surfaces.
India / Kashi Vishwanath (Varanasi) — Uttar Pradesh	Modeled/Simulated	2-4	10 x 8 x 12	Lingam alignment; sqrt(3) in dome.	Short RT60.	River influence.
India / Ramanathaswamy Temple (long corridors) — Tamil Nadu	Modeled/Simulated	5-7	205 x 10 x 5 (corridor)	Pillar grid 5:3; infinite perspective (φ).	Image-source corridors.	Echo-heavy.
India / Virupaksha Temple (Hampi) — Karnataka	Modeled/Simulated	4-6	50 x 25 x 15 (gopuram/base)	Ratios 2:1; ruins alignment.	Open decay.	Wind focus.
India / Ajanta Caves (selected halls) — Maharashtra	Measured (private/limited)	3-5	35 x 11 x 10	Chaitya arch vesica piscis.	Synthetic diffuse.	Rock-cut.
India / Elephanta Caves — Maharashtra	Modeled/Simulated	3-5	35 x 11 x 10	Trimurti sculpture φ proportions.	Like Ajanta.	Island caves.
India / Mahabodhi Temple (Bodh Gaya) — Bihar	Modeled/Simulated	3-4	55 x 15 x 15 (base & hall)	Pyramid ratios 4:3; stupa circle.	Low RT60.	Open stupa.
Nepal/Tibet / Jokhang Temple — Lhasa	Modeled/Simulated	4-6	20 x 15 x 10	Mandala plan; 8:5 (minor sixth).	Synthetic.	Chants resonance.
Nepal/Tibet / Potala Palace (chapel spaces) — Lhasa	Modeled/Simulated	3-5	8 x 6 x 5	Golden section in tiers.	Short RT60.	Palace rooms.
Nepal/Tibet / Tashi Lhunpo Monastery — Shigatse	Modeled/Simulated	5-7	30 x 20 x 15	Ratios 3:2; monastic grid.	Reverb like cathedral.	Chants.
Nepal / Boudhanath Stupa (inner gallery) — Kathmandu	Modeled/Simulated	2-4	36 x 10 x 5 (gallery)	Circle/square mandala; φ spiral.	Moderate echo.	Gallery.
Nepal / Swayambhunath (cave/chapel areas) — Kathmandu	Modeled/Simulated	3-5	10 x 5 x 4 (caves)	Hill alignments; vesica piscis.	Diffuse reverb.	Hilltop.
Tibet / Mount Kailash area caves — Ngari	Measured (private/limited)	2-4	10 x 5 x 4 (natural)	Sacred mountain circuit 1:φ.	Short RT60.	Echo.
Cambodia / Angkor Wat, outer galleries — Siem Reap	Measured (public)	4-6	187 x 215 x 10 (approx)	4:5 & 6:7 rectangles (multiples of 216m, precessional); cosmic mountain model.	Synthetic corridor; mode calc.	Stone echoes.
Cambodia / Angkor Wat, inner sanctum — Siem Reap	Measured (private/limited)	3-5	10 x 10 x 12	Central tower φ proportions.	Synthetic chamber.	Enclosed.
Cambodia / Bayon Temple — Siem Reap	Measured (private/limited)	4-6	45 x 45 x 15 (towers/space)	Face towers in mandala; 3:4:5 triangle.	Diffuse.	Faces.
Cambodia / Ta Prohm — Siem Reap	Modeled/Simulated	3-5	50 x 30 x 10	Halls variable; tree-integrated φ spirals.	Ruins reverb.	Jungle.
Cambodia / Preah Khan — Siem Reap	Modeled/Simulated	4-6	50 x 30 x 10	Linear alignments; golden mean.	Like Ta Prohm.	Overgrown.
Indonesia / Borobudur, central stupa — Java	Measured (public)	2-4	10 x 10 x 10 (volume proxy)	Mandala squares/circles; 9 levels (sacred 9).	Low RT60.	Bell-shaped.
Indonesia / Borobudur, upper terraces — Java	Measured (private/limited)	1-3	123 x 123 x 5 (terraces)	Ratios 5:4 (third); fractal stupas.	Minimal reverb.	Outdoor.
Indonesia / Prambanan Temple — Java	Modeled/Simulated	3-5	47 x 47 x 15	Main trimurti; φ in spires.	Like Angkor.	Complex.
Indonesia / Tanah Lot (shrine) — Bali	Modeled/Simulated	2-4	10 x 10 x 5	Sea alignments; wave harmonics.	Short.	Ocean.
China / Temple of Heaven (Hall of Prayer, Echo Wall) — Beijing	Modeled/Simulated	4-6	38 x 38 x 38	Circle (heaven); 3 tiers, ratios 9:3:1 (sacred 9).	Focused reflections.	Echo wall.
China / Mogao Caves (selected grottoes) — Dunhuang	Modeled/Simulated	3-5	5 x 4 x 3	Buddhist mandalas; vesica piscis.	Diffuse.	Desert.
China / Longmen Grottoes (chapel cavities) — Luoyang	Modeled/Simulated	2-4	5 x 4 x 3	Rock-cut φ proportions.	Short.	Like Ajanta.
Japan / Todai-ji (Daibutsuden) — Nara	Modeled/Simulated	5-8	57 x 50 x 48	Golden Buddha; hall ratios 6:5.	Long RT60.	Large hall.
Japan / Horyu-ji — Nara	Modeled/Simulated	4-6	32 x 20 x 15 (pagoda/hall)	Fibonacci tiers; sqrt(2) base.	Moderate.	Wooden.
Japan / Kiyomizu-dera — Kyoto	Modeled/Simulated	3-5	13 x 20 x 10 (stage)	Balcony alignments; 3:4:5.	Open reverb.	Waterfall.
Japan / Fushimi Inari (tunnel resonance) — Kyoto	Modeled/Simulated	2-4	long x 5 x 5 (tunnel proxy)	Torii arcs; infinite φ perspective.	Echo.	Gates.
Greece / Parthenon (reconstruction) — Athens	Modeled/Simulated	2-4	69.5 x 30.9 x 13.7	Facade golden ratio (width:height≈φ); 4:9 base (≈2.25:1, symbolic).	Low RT60; reconstructed.	Open ruins.
Greece / Temple of Apollo at Delphi — Delphi	Modeled/Simulated	3-5	23 x 11 x 9	Oracle ratios 2:1; mountain phi.	Echoes.	Oracle.
Greece / Theatre of Epidaurus — Peloponnese	Measured (public)	1-2	114 x 114 x 10 (open bowl)	Rows in φ progression; clarity via geometry.	Public studies.	Clarity.
Greece / Meteora Monasteries (chapels) — Thessaly	Modeled/Simulated	3-5	10 x 8 x 6	Cliff mandalas; 3:5 ratios.	Enclosed.	Wind.
Greece / Hosios Loukas Monastery — Boeotia	Modeled/Simulated	4-6	16 x 16 x 15 (dome hall)	Byzantine circles/squares.	Like Hagia.	Mosaics.
Italy / Pantheon — Rome	Measured (public)	6-8	43.3 x 43.3 x 43.3	Perfect sphere; oculus:base=1:6; 1:1:√2 relations.	Long RT60.	Oculus.
Italy / St. Peter’s Basilica — Vatican	Measured (private/limited)	8-10	136 x 42 x 42 (principal)	Michelangelo φ dome; cross plan.	Surveys.	Massive.
Italy / Florence Cathedral (Santa Maria del Fiore) — Florence	Modeled/Simulated	7-9	114 x 45 x 45	Dome octagon; φ ratios.	Cathedral reverb.	Dome.
Italy / Basilica di San Marco — Venice	Measured (public)	5-7	13 x 13 x 13 (per dome cell)	Byzantine 5 domes; mosaic diffusion.	IR packs.	Venetian.
Italy / Basilica di San Francesco — Assisi	Modeled/Simulated	4-6	80 x 20 x 20	Ratios 4:1; fresco harmony.	Moderate.	Franciscan.
Italy / San Vitale — Ravenna	Modeled/Simulated	5-7	16 x 16 x 15 (octagon)	Octagonal (sacred 8); central dome φ.	Like San Marco.	Byzantine.
France / Chartres Cathedral — Chartres	Measured (public)	5-8	73 x 16 x 37	Vesica windows; labyrinth φ spiral; 1:φ:φ².	Long RT60.	Gothic.
France / Notre-Dame de Paris (pre-2019) — Paris	Measured (public)	6-8	48 x 12 x 35	Rose windows circles; ratios 5:4.	Pre-fire surveys.	Restoration.
France / Mont-Saint-Michel Abbey — Normandy	Modeled/Simulated	5-7	50 x 20 x 20 (hall proxy)	Spire φ curve; island mandala.	Stone halls.	Tidal.
France / Sainte-Chapelle — Paris	Modeled/Simulated	4-6	36 x 11 x 20	Stained glass ratios 3:2; bright.	Chapel.	Glass.
Spain / Sagrada Família — Barcelona	Modeled/Simulated	6-8	90 x 45 x 60	Gaudi paraboloids; tree φ branching.	Organic reverb.	Unfinished.
Spain / Mezquita–Cathedral — Córdoba	Modeled/Simulated	5-7	180 x 130 x 15	856 columns (sacred 8); arches vesica.	Diffuse.	Mix.
Spain / Seville Cathedral — Seville	Modeled/Simulated	7-9	115 x 76 x 42	Largest Gothic; ratios 3:2.	Long RT60.	Scale.
Portugal / Jerónimos Monastery — Lisbon	Modeled/Simulated	5-7	90 x 30 x 25	Manueline knots; φ spirals.	Halls.	Nautical.
UK / Stonehenge (reconstruction chamber IR) — Wiltshire	Modeled/Simulated	1-3	33 x 33 x 5	Circles align solstices; Pythagorean triangles.	Low RT60; wind.	Chamber proxy.
Ireland / Newgrange passage tomb — County Meath	Measured (private/limited)	2-4	19 x 6 x 4 (passage & chamber)	Solstice alignment; sqrt(2) in kerb.	Echo tomb.	Solstice.
UK / Iona Abbey — Inner Hebrides	Modeled/Simulated	4-6	20 x 10 x 10	Celtic knots φ.	Moderate.	Celtic.
UK / Rosslyn Chapel — Midlothian	Modeled/Simulated	3-5	21 x 11 x 12	Carvings cubes (Platonic); ratios 2:1.	Diffuse.	Carved.
UK / Westminster Abbey — London	Modeled/Simulated	6-8	156 x 31 x 31	Henry VII fan vault φ.	Long nave.	Gothic.
UK / St Paul’s Cathedral — London	Modeled/Simulated	7-11	111 x 34 x 34 (principal)	Whisper gallery circle; 3:2 ratios.	Acoustics.	Dome.
UK / York Minster — York	Modeled/Simulated	6-9	80 x 15 x 30	Windows vesica; scale φ.	Long RT60.	Minster.
UK / Durham Cathedral — Durham	Modeled/Simulated	5-8	145 x 12 x 22	Norman arches; 3:4:5.	Robust.	Halls.
Germany / Cologne Cathedral — Cologne	Modeled/Simulated	7-10	144 x 86 x 43	Spires 157m (φ progression).	Very long.	Gothic.
Germany / Frauenkirche — Dresden	Modeled/Simulated	6-8	26 x 26 x 20 (dome cell)	Baroque circle/square.	Reconstructed.	Baroque.
Austria / St. Stephen’s Cathedral — Vienna	Modeled/Simulated	5-7	107 x 34 x 28	Roof tiles mosaic; ratios 3:1.	Moderate.	Gothic.
Hungary / Matthias Church — Budapest	Modeled/Simulated	4-6	60 x 23 x 20	Neo-Gothic φ tiles.	Colorful.	Coronation.
Turkey / Hagia Sophia — Istanbul	Measured (public)	10-11	55 x 31 x 31	Pendentive geometry; cross/circle; light cosmology.	Balloon IR; iconic.	Long RT60.
Turkey / Blue Mosque (Sultan Ahmed) — Istanbul	Modeled/Simulated	8-10	43 x 23 x 23	Similar to Hagia; 6 minarets (hexagon).	Like Hagia.	Tiles.
Turkey / Chora Church (Kariye) — Istanbul	Modeled/Simulated	5-7	15 x 10 x 10	Byzantine mosaics; vesica.	Fresco.	Byzantine.
Israel/Palestine / Church of the Holy Sepulchre — Jerusalem	Modeled/Simulated	4-6	30 x 30 x 20 (rotunda & bays)	Circle (resurrection); multi-room φ.	Variable.	Holy.
Israel/Palestine / Al-Aqsa / Dome of the Rock precinct — Jerusalem	Modeled/Simulated	3-5	20 x 20 x 15 (dome)	Octagon (8); golden dome ratios.	Low.	Precinct.
Syria / Ummayad Mosque — Damascus	Modeled/Simulated	5-7	157 x 97 x 15	Ratios 1.618 (φ); courtyard reverb.	Umayyad.	Courtyard.
Mexico / Chichén Itzá (El Castillo plaza acoustics) — Yucatán	Measured (public)	1-2	55.3 x 55.3 x 30	365 steps; chirp echo (diffraction); equinox serpents.	Clap chirp IR.	Outdoor.
Mexico / Teotihuacan (Temple of the Feathered Serpent) — Mexico	Modeled/Simulated	2-4	65 x 65 x 20	Pyramid ratios 4:3; serpent alignments.	Like Chichen.	Echo.
Mexico / Tulum Temple precinct — Quintana Roo	Modeled/Simulated	1-3	20 x 10 x 5 (precinct cell)	Coastal alignments; wave harmonics.	Low.	Coastal.
Peru / Machu Picchu (Sun Temple) — Cusco	Modeled/Simulated	2-4	10 x 10 x 5 (semi-circle cell)	Intihuatana solar; stone φ fittings.	Altitude.	Mountain.
Peru / Sacsayhuamán — Cusco	Modeled/Simulated	1-3	50 x 20 x 5	Walls massive; sqrt(3) angles.	Open.	Stones.
Mexico / Basilica of Guadalupe — Mexico City	Modeled/Simulated	5-7	100 x 50 x 20	Modern oval; Tepeyac hill; φ curves.	Moderate.	Modern.
USA / Mission San Carlos Borromeo — Carmel	Modeled/Simulated	3-5	30 x 10 x 10	Adobe arches; 3:2 ratios.	Colonial.	Adobe.
USA / Kiva spaces (Mesa Verde-type) — Southwest	Modeled/Simulated	2-4	7 x 7 x 5	Circular (unity); underground mandala.	Short.	Ceremonial.
Ethiopia / Lalibela Rock-Hewn Churches — Amhara	Measured (private/limited)	3-5	12 x 10 x 11	Cross plans; 1:1 (equality).	Cave-like.	Rock-cut.
Mali / Great Mosque of Djenné — Djenné	Modeled/Simulated	4-6	75 x 75 x 10	Mud-brick spirals; annual renewal (cycle).	Diffuse.	Sahel.
Zimbabwe / Great Zimbabwe (enclosures) — Masvingo	Modeled/Simulated	2-4	50 x 20 x 5	Walls curved; vesica-like ellipses.	Low.	Ruins.
"""

# ----------------------
# Parsing helpers
# ----------------------
def _norm(s:str) -> str:
    if s is None: return ""
    return s.replace("’","'").replace("‘","'").strip()

def parse_rt60_to_float(s:str) -> float:
    s = (s or "").strip()
    if not s: return 3.0
    s = s.replace("~","").replace("≈","")
    s = s.replace("–","-").replace("—","-")
    m = re.findall(r"(\d+(?:\.\d+)?)", s)
    if not m: return 3.0
    vals = [float(x) for x in m]
    if len(vals) == 1: return vals[0]
    return sum(vals)/len(vals)

def parse_dims_to_lwh(s:str) -> tuple[float,float,float]:
    """
    Try to coerce any dimension text to (L,W,H) meters.
    - '10.47 x 5.235 x 5.827'
    - '57x50x48'
    - 'Dome 31m diam, 55m high'
    - '205m long' -> (205, 10, 5) as corridor proxy
    - 'overall' / 'base' -> take numbers in order; if only 2, repeat min for H
    Fallback: (10,10,10)
    """
    if not s: return (10.0,10.0,10.0)
    s = s.lower().replace("×","x")
    # handle dome diameter/height
    diam = None
    height = None
    dmatch = re.search(r"(\d+(?:\.\d+)?)\s*m\s*(?:diam|diameter)", s)
    hmatch = re.search(r"(\d+(?:\.\d+)?)\s*m\s*(?:high|height)", s)
    if dmatch: diam = float(dmatch.group(1))
    if hmatch: height = float(hmatch.group(1))
    if diam is not None and height is not None:
        # approximate dome cell as (diam, diam, height)
        return (float(diam), float(diam), float(height))
    # corridor "long"
    lmatch = re.search(r"(\d+(?:\.\d+)?)\s*m\s*(?:long|length)", s)
    if lmatch:
        L = float(lmatch.group(1))
        return (L, 10.0, 5.0)
    # generic #'s
    nums = re.findall(r"(\d+(?:\.\d+)?)", s)
    vals = [float(x) for x in nums]
    if len(vals) >= 3:
        return (vals[0], vals[1], vals[2])
    if len(vals) == 2:
        # assume base rectangle with modest height
        H = min(vals)
        return (vals[0], vals[1], H)
    if len(vals) == 1:
        v = vals[0]
        return (v, v, v/2.0 if v>6 else 5.0)
    return (10.0,10.0,10.0)

def parse_region_and_name(s:str) -> tuple[str,str]:
    # input like "Egypt / Great Pyramid, King’s Chamber — Giza"
    s = _norm(s)
    if " / " in s:
        region, rest = s.split(" / ", 1)
    else:
        region, rest = "Unknown", s
    name = rest
    return (region.strip(), name.strip())

def parse_tsv_block(tsv:str):
    lines = [l for l in tsv.splitlines() if l.strip()]
    header = lines[0].split("\t")
    idx = {h:i for i,h in enumerate(header)}
    rows = []
    for line in lines[1:]:
        cols = line.split("\t")
        def g(field): 
            return cols[idx[field]].strip() if field in idx and idx[field] < len(cols) else ""
        region_site = g("Region/Site")
        status = g("Status")
        rt = g("Estimated RT60 (s)")
        dims = g("Dimensions (m, approx. LxWxH)")
        notes_geom = g("Sacred Geometry Notes")
        sim_method = g("Simulation Method")
        sources = g("Notes/Sources")
        region, site = parse_region_and_name(region_site)
        rt60 = parse_rt60_to_float(rt)
        L,W,H = parse_dims_to_lwh(dims)
        rows.append({
            "region": region,
            "site": site,
            "status": status,
            "rt60": float(rt60),
            "dims": [float(L), float(W), float(H)],
            "geometry": notes_geom,
            "sim_method": sim_method,
            "sources": sources,
            "parse_notes": None  # reserved for parser hints if needed
        })
    return rows

# Build site dict + countries/regions map
SITE_ROWS = parse_tsv_block(DATA_TSV)

def _key(s): return _norm(s)

SACRED_SITES = {}
REGION_MAP = {}  # {Region: [sites...]}

for r in SITE_ROWS:
    k = _key(r["site"])
    if k in SACRED_SITES:
        # keep first; ignore duplicates
        continue
    SACRED_SITES[k] = {
        "rt60": r["rt60"],
        "dims": r["dims"],
        "geometry": r["geometry"],
        "status": r["status"],
        "sim_method": r["sim_method"],
        "sources": r["sources"],
        "region": r["region"],
    }
    REGION_MAP.setdefault(r["region"], []).append(r["site"])

# ============================================================
# Acoustic analytics (lightweight; no audio)
# ============================================================
C_SOUND = 343.0
STD_BANDS = [125, 250, 500, 1000, 2000, 4000]

def np_to_native(x):
    if isinstance(x, np.ndarray): return x.tolist()
    if isinstance(x, (np.floating, np.integer)): return x.item()
    if isinstance(x, dict): return {k: np_to_native(v) for k,v in x.items()}
    if isinstance(x, (list, tuple)): return [np_to_native(v) for v in x]
    return x

def room_volume(dims):
    L, W, H = dims
    return float(L*W*H)

def room_surface(dims):
    L, W, H = dims
    return float(2.0*(L*W + L*H + W*H))

def avg_absorption_from_rt60(rt60, V, S):
    if rt60 <= 0 or S <= 0: return 0.2
    a = 0.161 * V / (rt60 * S)
    return float(min(max(a, 0.02), 0.9))

def rt60_tilt_by_band(base_rt, bands):
    out = {}
    for f in bands:
        tilt = -0.18 * math.log10(max(f, 125)/500.0)
        out[str(int(f))] = float(max(0.2, base_rt + tilt))
    return out

def nearest_band_rt60(rt60_by_band, f_hz):
    bands = [int(b) for b in rt60_by_band.keys()]
    b = min(bands, key=lambda x: abs(x - f_hz))
    return float(rt60_by_band[str(b)])

def schroeder_frequency(rt60, V):
    if V <= 0 or rt60 <= 0: return None
    return 2000.0 * math.sqrt(rt60 / V)

def modal_type(nx, ny, nz):
    npos = int(nx > 0) + int(ny > 0) + int(nz > 0)
    return "axial" if npos == 1 else ("tangential" if npos == 2 else "oblique")

def modal_list(dims, fmax=2000.0, top_n=24, rt60_by_band=None):
    Lx, Ly, Lz = dims
    modes = []
    for nx in range(0, 12):
        for ny in range(0, 12):
            for nz in range(0, 12):
                if nx == ny == nz == 0: continue
                f = (C_SOUND/2.0) * math.sqrt(
                    (nx/max(Lx,1e-6))**2 +
                    (ny/max(Ly,1e-6))**2 +
                    (nz/max(Lz,1e-6))**2
                )
                if f <= fmax:
                    T_here = nearest_band_rt60(rt60_by_band, f) if rt60_by_band else 3.0
                    B = 13.815510558 / (math.pi * max(T_here, 1e-6))  # Hz
                    peak_e = (1.0/max(B,1e-6)) * (1.0/max(f,50.0))
                    modes.append({
                        "freq_hz": float(f),
                        "nx": nx, "ny": ny, "nz": nz,
                        "type": modal_type(nx, ny, nz),
                        "bandwidth_hz": float(B),
                        "gauss_sigma_hz": float(B/2.355),
                        "rel_energy": float(peak_e)
                    })
    modes.sort(key=lambda m: (m["freq_hz"], -m["rel_energy"]))
    sel = modes[:int(top_n)]
    esum = sum(m["rel_energy"] for m in sel) or 1.0
    for m in sel:
        m["rel_energy"] = float(m["rel_energy"]/esum)
    return sel

def early_reflections(dims, alpha_avg, n=6):
    L, W, H = dims
    paths = [
        0.0,
        2*L, 2*W, 2*H,
        2*math.sqrt(L*L + W*W),
        2*math.sqrt(L*L + H*H),
    ][:max(1,n)]
    taps = []
    for d in paths:
        t_ms = (d/C_SOUND)*1000.0
        if d == 0.0:
            e = 1.0
        else:
            bounces = 1 if d in (2*L,2*W,2*H) else 2
            reflectance = (1.0 - alpha_avg)**bounces
            e = reflectance / max(d*d, 1e-6)
        taps.append([float(t_ms), float(e)])
    total = sum(e for _,e in taps) or 1.0
    return [[t, e/total] for t,e in taps]

# ============================================================
# Routes
# ============================================================
@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to Sanctra API (lightweight simulation only)",
        "endpoints": ["/health", "/sites", "/sites-by-country", "/site-info?site=...", "/generate-ir"],
        "note": "POST /generate-ir returns compact JSON acoustic analytics (no audio)."
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/sites", methods=["GET"])
def get_sites():
    return jsonify({"sites": sorted(SACRED_SITES.keys())})

@app.route("/sites-by-country", methods=["GET"])
def sites_by_country():
    # Derived from Region column (left of ' / ' in 'Region/Site')
    mapping = {}
    for region, names in REGION_MAP.items():
        mapping[region] = sorted(names)
    return jsonify(mapping)

@app.route("/site-info", methods=["GET"])
def site_info():
    site = request.args.get("site", type=str)
    if not site:
        return jsonify({"error":"Missing 'site' query parameter","hint":"Use /sites to list valid names"}), 400
    site_k = _key(site)
    if site_k not in SACRED_SITES:
        return jsonify({"error": f"Site '{site}' not found","hint":"Use /sites to list valid names"}), 404
    info = dict(SACRED_SITES[site_k])
    info_out = {
        "site": site_k,
        **info
    }
    return jsonify(np_to_native(info_out)), 200

@app.route("/generate-ir", methods=["POST"])
def generate_ir():
    """
    Simulation-only endpoint: returns a compact JSON "acoustic fingerprint" for a site.
    NO audio is returned. Designed to be light on CPU and memory.

    Body JSON:
    {
      "site": "<name>",            # required (use /sites)
      "bands": [125,250,500,1000,2000,4000],  # optional
      "fmax_hz": 2000.0,           # optional
      "modes_top_n": 24            # optional
    }
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        site = data.get("site")
        if not site:
            return jsonify({"error":"Missing 'site'"}), 400
        site_k = _key(site)
        if site_k not in SACRED_SITES:
            return jsonify({"error": f"Site '{site}' not found"}), 404

        bands = data.get("bands", STD_BANDS)
        try:
            bands = [int(b) for b in bands]
        except Exception:
            return jsonify({"error":"bands must be a list of integers"}), 400

        fmax = float(data.get("fmax_hz", 2000.0))
        top_n = int(data.get("modes_top_n", 24))

        info = SACRED_SITES[site_k]
        dims = [float(x) for x in info["dims"]]
        base_rt = float(info["rt60"])
        V = room_volume(dims)
        S = room_surface(dims)

        rt60_by_band = rt60_tilt_by_band(base_rt, bands)
        alpha_avg = avg_absorption_from_rt60(base_rt, V, S)
        fs = schroeder_frequency(base_rt, V)
        tail_ref = float(min(3.0, max(1.0, base_rt)))

        payload = {
            "site": site_k,
            "region": info.get("region",""),
            "status": info.get("status",""),
            "dims_m": dims,
            "volume_m3": V,
            "surface_area_m2": S,
            "absorption_avg": alpha_avg,
            "rt60_s_by_band": rt60_by_band,
            "schroeder_freq_hz": fs,
            "modal_summary": modal_list(dims, fmax=fmax, top_n=top_n, rt60_by_band=rt60_by_band),
            "early_reflection_taps": early_reflections(dims, alpha_avg, n=6),
            "ir_tail_sec_reference": tail_ref,  # reference only, not returned as audio
            "method": "simulation_only_shoebox_analytics",
            "notes": info.get("geometry",""),
            "sim_method": info.get("sim_method",""),
            "sources": info.get("sources","")
        }
        return jsonify(np_to_native(payload)), 200
    except Exception as e:
        return jsonify({"error":"simulation failed","detail":str(e)}), 500

# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
