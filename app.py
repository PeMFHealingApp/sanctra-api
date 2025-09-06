from flask import Flask, jsonify, request, url_for
import unicodedata
import os
import json
import math

app = Flask(__name__)

from flask_cors import CORS

CORS(
    app,
    resources={r"/*": {"origins": [
        "https://pemfhealingapp.github.io",
        "http://localhost:8080",   # keep for local testing
    ]}},
    supports_credentials=False
)


# -----------------------------
# Local JSON path - single source of truth
# -----------------------------
LOCAL_JSON_PATH = os.path.join(os.path.dirname(__file__), "sacred_sites.json")

# -----------------------------
# Image manifest (served from /static/site-images)
# -----------------------------
MANIFEST_PATH = os.path.join(os.path.dirname(__file__), "static", "site-images", "manifest.json")

def load_image_manifest():
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

IMAGE_MANIFEST = load_image_manifest()

# -----------------------------
# Text normalization
# -----------------------------

def norm_text(s: str) -> str:
    if not isinstance(s, str):
        return s
    # unify quotes and dashes, squeeze spaces, lowercase
    s = (
        s.replace("’", "'")
         .replace("‘", "'")
         .replace("–", "-")
         .replace("—", "-")
         .strip()
         .lower()
    )
    return " ".join(s.split())

# also used for manifest lookups (case/quote-insensitive)

def _norm_key(s: str) -> str:
    # normalize unicode and unify quotes/spaces
    return unicodedata.normalize("NFKC", (s or "").replace("’", "'").replace("‘", "'").strip()).lower()

# -----------------------------
# Numpy-safe JSON conversion
# -----------------------------

def np_to_native(x):
    if isinstance(x, (list, tuple)):
        return [np_to_native(i) for i in x]
    if isinstance(x, dict):
        return {k: np_to_native(v) for k, v in x.items()}
    if isinstance(x, (float, int)):
        return float(x)
    return x

# -----------------------------
# JSON parsing helpers
# -----------------------------
DEFAULT_DISCLAIMER = (
    "The information provided is for educational and exploratory purposes only "
    "and should not be considered medical advice. Consult a healthcare professional "
    "before using any healing practices."
)

def _parse_payload(data: dict):
    """
    Accept either:
      { "sacred_sites": [ {site, region|country, ...}, ...], "disclaimer": "..." }
    or a bare list:
      [ {site, region|country, ...}, ... ]
    """
    if isinstance(data, list):
        sites_list = data
        disclaimer = DEFAULT_DISCLAIMER
    else:
        sites_list = data.get("sacred_sites", [])
        disclaimer = data.get("disclaimer", DEFAULT_DISCLAIMER)
    return sites_list, disclaimer


def _build_maps(sites_list):
    sacred_sites = {}
    region_map = {}
    for site in sites_list:
        site_name = site.get("site", "")
        key = norm_text(site_name)
        if not key:
            # skip malformed entries without a site name
            continue

        # accept "region" or "country"
        region_or_country = site.get("region") or site.get("country") or ""

        sacred_sites[key] = site
        region_map.setdefault(region_or_country, []).append(site_name)

    return sacred_sites, region_map


def load_sacred_sites():
    try:
        with open(LOCAL_JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        sites_list, disclaimer = _parse_payload(data)
        sacred_sites, region_map = _build_maps(sites_list)
        if sacred_sites:
            return sacred_sites, region_map, disclaimer
    except Exception as e:
        print("Failed to load sacred_sites.json:", e)

    # last-resort empty structures
    return {}, {}, DEFAULT_DISCLAIMER

# -----------------------------
# Load once on startup
# -----------------------------
SACRED_SITES, REGION_MAP, DISCLAIMER = load_sacred_sites()

# -----------------------------
# Acoustic analytics (lightweight, no audio)
# -----------------------------
C_SOUND = 343.0
STD_BANDS = [125, 250, 500, 1000, 2000, 4000]

def room_volume(dims):
    L, W, H = dims
    return float(L * W * H)

def room_surface(dims):
    L, W, H = dims
    return float(2.0 * (L * W + L * H + W * H))

def avg_absorption_from_rt60(rt60, V, S):
    if rt60 <= 0 or S <= 0:
        return 0.2
    a = 0.161 * V / (rt60 * S)
    return float(min(max(a, 0.02), 0.9))

def rt60_tilt_by_band(base_rt, bands):
    out = {}
    for f in bands:
        tilt = -0.18 * math.log10(max(f, 125) / 500.0)
        out[str(int(f))] = float(max(0.2, base_rt + tilt))
    return out

def nearest_band_rt60(rt60_by_band, f_hz):
    bands = [int(b) for b in rt60_by_band.keys()]
    b = min(bands, key=lambda x: abs(x - f_hz))
    return float(rt60_by_band[str(b)])

def schroeder_frequency(rt60, V):
    if V <= 0 or rt60 <= 0:
        return None
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
                if nx == ny == nz == 0:
                    continue
                f = (C_SOUND / 2.0) * math.sqrt(
                    (nx / max(Lx, 1e-6)) ** 2 + (ny / max(Ly, 1e-6)) ** 2 + (nz / max(Lz, 1e-6)) ** 2
                )
                if f <= fmax:
                    T_here = nearest_band_rt60(rt60_by_band, f) if rt60_by_band else 3.0
                    B = 13.815510558 / (math.pi * max(T_here, 1e-6))  # Hz
                    peak_e = (1.0 / max(B, 1e-6)) * (1.0 / max(f, 50.0))
                    modes.append({
                        "freq_hz": float(f),
                        "nx": nx, "ny": ny, "nz": nz,
                        "type": modal_type(nx, ny, nz),
                        "bandwidth_hz": float(B),
                        "gauss_sigma_hz": float(B / 2.355),
                        "rel_energy": float(peak_e)
                    })
    modes.sort(key=lambda m: (m["freq_hz"], -m["rel_energy"]))
    sel = modes[:int(top_n)]
    esum = sum(m["rel_energy"] for m in sel) or 1.0
    for m in sel:
        m["rel_energy"] = float(m["rel_energy"] / esum)
    return sel

def early_reflections(dims, alpha_avg, n=6):
    L, W, H = dims
    paths = [
        0.0,
        2 * L, 2 * W, 2 * H,
        2 * math.sqrt(L * L + W * W),
        2 * math.sqrt(L * L + H * H),
    ][:max(1, n)]
    taps = []
    for d in paths:
        t_ms = (d / C_SOUND) * 1000.0
        if d == 0.0:
            e = 1.0
        else:
            bounces = 1 if d in (2 * L, 2 * W, 2 * H) else 2
            reflectance = (1.0 - alpha_avg) ** bounces
            e = reflectance / max(d * d, 1e-6)
        taps.append([float(t_ms), float(e)])
    total = sum(e for _, e in taps) or 1.0
    return [[t, e / total] for t, e in taps]

# -----------------------------
# Image helpers
# -----------------------------

def image_filename_for_site(site_name: str) -> str | None:
    """
    Look up an image filename for a site:
    1) exact key match in IMAGE_MANIFEST
    2) normalized-title match against IMAGE_MANIFEST keys
    """
    if not site_name:
        return None
    # exact title match
    entry = IMAGE_MANIFEST.get(site_name)
    if isinstance(entry, dict) and entry.get("file"):
        return entry["file"]
    # normalized title match
    nk = _norm_key(site_name)
    for title, meta in IMAGE_MANIFEST.items():
        if isinstance(meta, dict) and meta.get("file") and _norm_key(title) == nk:
            return meta["file"]
    return None

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to Sanctra API (lightweight simulation only)",
        "endpoints": [
            "/health",
            "/reload",
            "/sites",
            "/countries",
            "/sites-by-country",
            "/sites-for-country?country=...",
            "/site-info?site=...",
            "/site-image?site=...",
            "/generate-ir"
        ],
        "note": "POST /generate-ir returns compact JSON acoustic analytics.",
        "cache_sizes": {
            "sites": len(SACRED_SITES),
            "countries": len(REGION_MAP)
        },
        "disclaimer": DISCLAIMER
    })

@app.route("/health", methods=["GET"])
def health():
    ok = bool(SACRED_SITES)
    return jsonify({"status": "ok" if ok else "degraded", "sites_cached": len(SACRED_SITES)}), 200

@app.route("/reload", methods=["POST"])
def reload_cache():
    global SACRED_SITES, REGION_MAP, DISCLAIMER
    SACRED_SITES, REGION_MAP, DISCLAIMER = load_sacred_sites()
    # also reload images in case new files were deployed
    global IMAGE_MANIFEST
    IMAGE_MANIFEST = load_image_manifest()
    return jsonify({"reloaded": True, "sites": len(SACRED_SITES), "images": len(IMAGE_MANIFEST)}), 200

@app.route("/sites", methods=["GET"])
def get_sites():
    names = [info.get("site", k) for k, info in SACRED_SITES.items()]
    return jsonify({"sites": sorted(names)})

@app.route("/sites-by-country", methods=["GET"])
def sites_by_country():
    mapping = {region: sorted(names) for region, names in sorted(REGION_MAP.items())}
    return jsonify(mapping)

@app.route("/countries", methods=["GET"])
def list_countries():
    return jsonify({"countries": sorted(REGION_MAP.keys())})

@app.route("/sites-for-country", methods=["GET"])
def sites_for_country():
    country = request.args.get("country", type=str)
    if not country:
        return jsonify({"error": "Missing 'country'"}), 400
    lc_map = {norm_text(r): r for r in REGION_MAP.keys()}
    key = lc_map.get(norm_text(country))
    if not key:
        return jsonify({"error": f"Unknown country '{country}'", "hint": "GET /countries"}), 404
    return jsonify({"country": key, "sites": sorted(REGION_MAP[key])}), 200

@app.route("/site-info", methods=["GET"])
def site_info():
    site = request.args.get("site", type=str)
    if not site:
        return jsonify({"error": "Missing 'site' query parameter", "hint": "Use /sites to list valid names"}), 400
    site_k = norm_text(site)
    if site_k not in SACRED_SITES:
        return jsonify({"error": f"Site '{site}' not found", "hint": "Use /sites to list valid names"}), 404

    info = SACRED_SITES[site_k]
    # allow alternate keys if present
    geometry_notes = info.get("geometry", info.get("sacred_geometry_notes", ""))
    sim_method = info.get("sim_method", info.get("simulation_method", ""))

    display_name = info.get("site", site)
    img_file = image_filename_for_site(display_name)

    info_out = {
        "site": display_name,
        "region": info.get("region", info.get("country", "")),
        "status": info.get("status", ""),
        "rt60": info.get("rt60"),
        "dims": info.get("dims"),
        "geometry": geometry_notes,
        "description": info.get("description", ""),
        "why_sacred": info.get("why_sacred", ""),
        "who_for": info.get("who_for", ""),
        "health_benefits": info.get("health_benefits", ""),
        "sim_method": sim_method,
        "sources": info.get("sources", ""),
        "image_url": (url_for("static", filename=f"site-images/{img_file}", _external=True) if img_file else None),
        "disclaimer": DISCLAIMER
    }
    return jsonify(np_to_native(info_out)), 200

@app.route("/site-image", methods=["GET"])
def site_image():
    site = request.args.get("site", type=str)
    if not site:
        return jsonify({"error": "Missing 'site' query parameter"}), 400

    # 1) Try to resolve directly from the manifest by title
    filename = image_filename_for_site(site)

    # 2) If not found, try via SACRED_SITES canonical display name
    if not filename:
        site_k = _norm_key(site)
        if site_k in SACRED_SITES:
            display_name = SACRED_SITES[site_k].get("site", site)
            filename = image_filename_for_site(display_name)
            site = display_name  # for the response

    if filename:
        return jsonify({
            "site": site,
            "image_url": url_for("static", filename=f"site-images/{filename}", _external=True)
        }), 200

    return jsonify({
        "error": f"No image found for '{site}'",
        "hint": "Check spelling or ensure it exists in static/site-images/manifest.json"
    }), 404

@app.route("/generate-ir", methods=["POST"])
def generate_ir():
    try:
        data = request.get_json(force=True, silent=True) or {}
        site = data.get("site")
        if not site:
            return jsonify({"error": "Missing 'site'"}), 400

        site_k = norm_text(site)
        if site_k not in SACRED_SITES:
            return jsonify({"error": f"Site '{site}' not found"}), 404

        bands = data.get("bands", STD_BANDS)
        bands = [int(b) for b in bands]

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

        geometry_notes = info.get("geometry", info.get("sacred_geometry_notes", ""))
        sim_method = info.get("sim_method", info.get("simulation_method", ""))

        payload = {
            "site": info.get("site", site),
            "region": info.get("region", info.get("country", "")),
            "status": info.get("status", ""),
            "dims_m": dims,
            "volume_m3": V,
            "surface_area_m2": S,
            "absorption_avg": alpha_avg,
            "rt60_s_by_band": rt60_by_band,
            "schroeder_freq_hz": fs,
            "modal_summary": modal_list(dims, fmax=fmax, top_n=top_n, rt60_by_band=rt60_by_band),
            "early_reflection_taps": early_reflections(dims, alpha_avg, n=6),
            "ir_tail_sec_reference": tail_ref,
            "method": "simulation_only_shoebox_analytics",
            "notes": geometry_notes,
            "description": info.get("description", ""),
            "why_sacred": info.get("why_sacred", ""),
            "who_for": info.get("who_for", ""),
            "health_benefits": info.get("health_benefits", ""),
            "sim_method": sim_method,
            "sources": info.get("sources", ""),
            "disclaimer": DISCLAIMER
        }
        return jsonify(np_to_native(payload)), 200
    except ValueError:
        return jsonify({"error": "bands must be a list of integers"}), 400
    except Exception as e:
        return jsonify({"error": "simulation failed", "detail": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
