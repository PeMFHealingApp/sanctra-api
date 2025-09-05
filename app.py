from flask import Flask, jsonify, request
import os
import requests
import json
import math

app = Flask(__name__)

# URL to the raw sacred_sites.json file on GitHub
SACRED_SITES_JSON_URL = "https://raw.githubusercontent.com/PeMFHealingApp/sanctra-api/main/sacred_sites.json"

# Fetch and load the JSON data
def load_sacred_sites():
    try:
        response = requests.get(SACRED_SITES_JSON_URL)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        sacred_sites = {site["site"].lower().replace("’", "'").replace("‘", "'").strip(): site for site in data["sacred_sites"]}
        region_map = {}
        for site in data["sacred_sites"]:
            region_map.setdefault(site["region"], []).append(site["site"])
        return sacred_sites, region_map, data["disclaimer"]
    except Exception as e:
        return {}, {}, "The information provided is for educational and exploratory purposes only and should not be considered medical advice. Consult a healthcare professional before using any healing practices."

# Load the data on startup
SACRED_SITES, REGION_MAP, DISCLAIMER = load_sacred_sites()

# Acoustic analytics (lightweight; no audio)
C_SOUND = 343.0
STD_BANDS = [125, 250, 500, 1000, 2000, 4000]

def np_to_native(x):
    if isinstance(x, (list, tuple)):
        return [np_to_native(i) for i in x]
    if isinstance(x, dict):
        return {k: np_to_native(v) for k, v in x.items()}
    if isinstance(x, (float, int)):
        return float(x)
    return x

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

# Routes
@app.route("/")
def home():
    return jsonify({
        "message": "Welcome to Sanctra API (lightweight simulation only)",
        "endpoints": [
            "/health",
            "/sites",
            "/countries",
            "/sites-by-country",
            "/sites-for-country?country=...",
            "/site-info?site=...",
            "/generate-ir"
        ],
        "note": "POST /generate-ir returns compact JSON acoustic analytics (no audio).",
        "disclaimer": DISCLAIMER
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

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
    lc_map = {r.lower(): r for r in REGION_MAP.keys()}
    key = lc_map.get(country.lower())
    if not key:
        return jsonify({"error": f"Unknown country '{country}'", "hint": "GET /countries"}), 404
    return jsonify({"country": key, "sites": sorted(REGION_MAP[key])}), 200

@app.route("/site-info", methods=["GET"])
def site_info():
    site = request.args.get("site", type=str)
    if not site:
        return jsonify({"error": "Missing 'site' query parameter", "hint": "Use /sites to list valid names"}), 400
    site_k = site.lower().replace("’", "'").replace("‘", "'").strip()
    if site_k not in SACRED_SITES:
        return jsonify({"error": f"Site '{site}' not found", "hint": "Use /sites to list valid names"}), 404
    info = SACRED_SITES[site_k]
    info_out = {
        "site": info.get("site", site_k),
        "region": info.get("region", ""),
        "status": info.get("status", ""),
        "rt60": info.get("rt60"),
        "dims": info.get("dims"),
        "geometry": info.get("geometry", ""),
        "description": info.get("description", ""),
        "why_sacred": info.get("why_sacred", ""),
        "who_for": info.get("who_for", ""),
        "health_benefits": info.get("health_benefits", ""),
        "sim_method": info.get("sim_method", ""),
        "sources": info.get("sources", "")
    }
    return jsonify(np_to_native(info_out)), 200

@app.route("/generate-ir", methods=["POST"])
def generate_ir():
    try:
        data = request.get_json(force=True, silent=True) or {}
        site = data.get("site")
        if not site:
            return jsonify({"error": "Missing 'site'"}), 400
        site_k = site.lower().replace("’", "'").replace("‘", "'").strip()
        if site_k not in SACRED_SITES:
            return jsonify({"error": f"Site '{site}' not found"}), 404
        bands = data.get("bands", STD_BANDS)
        try:
            bands = [int(b) for b in bands]
        except Exception:
            return jsonify({"error": "bands must be a list of integers"}), 400
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
            "site": info.get("site", site_k),
            "region": info.get("region", ""),
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
            "notes": info.get("geometry", ""),
            "description": info.get("description", ""),
            "why_sacred": info.get("why_sacred", ""),
            "who_for": info.get("who_for", ""),
            "health_benefits": info.get("health_benefits", ""),
            "sim_method": info.get("sim_method", ""),
            "sources": info.get("sources", "")
        }
        return jsonify(np_to_native(payload)), 200
    except Exception as e:
        return jsonify({"error": "simulation failed", "detail": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
