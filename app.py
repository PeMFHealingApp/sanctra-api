from flask import Flask, jsonify, request
import numpy as np
import scipy.signal as signal
import os

app = Flask(__name__)

# Dictionary of sacred sites with RT60, dimensions, and geometry notes
SACRED_SITES = {
    "Great Pyramid King's Chamber": {
        "rt60": 2.5,
        "dims": [10.47, 5.235, 5.827],
        "geometry": "Golden ratio (height:width≈φ/2), length:width=2:1, ~121 Hz resonance"
    },
    "Great Pyramid Queen's Chamber": {
        "rt60": 1.5,
        "dims": [5.75, 5.23, 6.23],
        "geometry": "Similar to King’s; sqrt(5) in height; niche ratios follow φ"
    },
    "Great Pyramid Grand Gallery": {
        "rt60": 3.5,
        "dims": [46.68, 2.09, 8.68],
        "geometry": "Slope angle ~26° (seked 5.5, related to sqrt(φ)); length:height≈φ^2"
    },
    "Pyramid of Khafre": {
        "rt60": 2.5,
        "dims": [10.0, 5.0, 6.0],
        "geometry": "Pi/phi integrations like Great Pyramid"
    },
    "Abu Simbel Temple": {
        "rt60": 5.0,
        "dims": [18.0, 16.4, 8.0],
        "geometry": "Rock-cut with solar alignments; ratios 9:5 (≈φ)"
    },
    "Karnak Temple Hypostyle Hall": {
        "rt60": 6.5,
        "dims": [50.0, 103.0, 24.0],
        "geometry": "Column grid follows 1:√2; vast scale encodes solar ratios"
    },
    "Luxor Temple": {
        "rt60": 5.0,
        "dims": [190.0, 55.0, 15.0],
        "geometry": "Avenue aligns with Nile; pylon ratios 4:3 (fifth interval)"
    },
    "Dendera Temple of Hathor": {
        "rt60": 4.0,
        "dims": [10.0, 8.0, 6.0],
        "geometry": "Zodiac ceiling; vesica piscis in layouts"
    },
    "Philae Temple": {
        "rt60": 5.0,
        "dims": [32.0, 18.0, 12.0],
        "geometry": "Island layout; golden spiral in colonnades"
    },
    "Kailasa Temple Ellora": {
        "rt60": 4.0,
        "dims": [60.0, 30.0, 33.0],
        "geometry": "Rock-cut mandala; ratios 1:φ:φ^2 (Fibonacci)"
    },
    "Konark Sun Temple": {
        "rt60": 5.0,
        "dims": [229.0, 128.0, 20.0],
        "geometry": "Chariot form; 12 wheels (zodiac), ratios 7:4 (solar)"
    },
    "Brihadeeswarar Temple": {
        "rt60": 6.0,
        "dims": [60.0, 30.0, 30.0],
        "geometry": "Height:base≈2:1; shikhara follows sqrt(2)"
    },
    "Meenakshi Temple": {
        "rt60": 5.0,
        "dims": [50.0, 30.0, 15.0],
        "geometry": "Gopuram ratios φ; mandala plan"
    },
    "Golden Temple": {
        "rt60": 4.0,
        "dims": [20.0, 20.0, 15.0],
        "geometry": "Square (stability); dome φ curve"
    },
    "Jagannath Temple": {
        "rt60": 5.0,
        "dims": [65.0, 20.0, 20.0],
        "geometry": "Vimana ratios 3:2 (fifth)"
    },
    "Kandariya Mahadev": {
        "rt60": 4.0,
        "dims": [31.0, 15.0, 15.0],
        "geometry": "Shikharas in φ progression"
    },
    "Kashi Vishwanath": {
        "rt60": 3.0,
        "dims": [10.0, 8.0, 12.0],
        "geometry": "Lingam alignment; sqrt(3) in dome"
    },
    "Ramanathaswamy Temple": {
        "rt60": 6.0,
        "dims": [205.0, 10.0, 5.0],
        "geometry": "Pillar grid 5:3; infinite perspective (φ)"
    },
    "Virupaksha Temple": {
        "rt60": 5.0,
        "dims": [50.0, 25.0, 15.0],
        "geometry": "Ratios 2:1; ruins alignment"
    },
    "Ajanta Caves": {
        "rt60": 4.0,
        "dims": [35.0, 11.0, 10.0],
        "geometry": "Chaitya arch vesica piscis"
    },
    "Elephanta Caves": {
        "rt60": 4.0,
        "dims": [35.0, 11.0, 10.0],
        "geometry": "Trimurti sculpture φ proportions"
    },
    "Mahabodhi Temple": {
        "rt60": 3.5,
        "dims": [55.0, 15.0, 15.0],
        "geometry": "Pyramid ratios 4:3; stupa circle"
    },
    "Jokhang Temple": {
        "rt60": 5.0,
        "dims": [20.0, 15.0, 10.0],
        "geometry": "Mandala plan; 8:5 (minor sixth)"
    },
    "Potala Palace Chapel": {
        "rt60": 4.0,
        "dims": [8.0, 6.0, 5.0],
        "geometry": "Golden section in tiers"
    },
    "Tashi Lhunpo Monastery": {
        "rt60": 6.0,
        "dims": [30.0, 20.0, 15.0],
        "geometry": "Ratios 3:2; monastic grid"
    },
    "Boudhanath Stupa Gallery": {
        "rt60": 3.0,
        "dims": [36.0, 10.0, 5.0],
        "geometry": "Circle/square mandala; φ spiral"
    },
    "Swayambhunath Caves": {
        "rt60": 4.0,
        "dims": [10.0, 5.0, 4.0],
        "geometry": "Hill alignments; vesica piscis"
    },
    "Mount Kailash Caves": {
        "rt60": 3.0,
        "dims": [10.0, 5.0, 4.0],
        "geometry": "Sacred mountain circuit 1:φ"
    },
    "Angkor Wat Outer Galleries": {
        "rt60": 5.0,
        "dims": [187.0, 215.0, 10.0],
        "geometry": "4:5 & 6:7 rectangles (multiples of 216m, precessional); cosmic mountain model"
    },
    "Angkor Wat Inner Sanctum": {
        "rt60": 4.0,
        "dims": [10.0, 10.0, 12.0],
        "geometry": "Central tower φ proportions"
    },
    "Bayon Temple": {
        "rt60": 5.0,
        "dims": [45.0, 45.0, 15.0],
        "geometry": "Face towers in mandala; 3:4:5 triangle"
    },
    "Ta Prohm": {
        "rt60": 4.0,
        "dims": [50.0, 30.0, 10.0],
        "geometry": "Tree-integrated φ spirals"
    },
    "Preah Khan": {
        "rt60": 5.0,
        "dims": [50.0, 30.0, 10.0],
        "geometry": "Linear alignments; golden mean"
    },
    "Borobudur Central Stupa": {
        "rt60": 3.0,
        "dims": [10.0, 10.0, 10.0],
        "geometry": "Mandala squares/circles; 9 levels (sacred 9)"
    },
    "Borobudur Upper Terraces": {
        "rt60": 2.0,
        "dims": [123.0, 123.0, 5.0],
        "geometry": "Ratios 5:4 (third); fractal stupas"
    },
    "Prambanan Temple": {
        "rt60": 4.0,
        "dims": [47.0, 47.0, 15.0],
        "geometry": "Trimurti triangles; φ in spires"
    },
    "Tanah Lot Shrine": {
        "rt60": 3.0,
        "dims": [10.0, 10.0, 5.0],
        "geometry": "Sea alignments; wave harmonics"
    },
    "Temple of Heaven": {
        "rt60": 5.0,
        "dims": [38.0, 38.0, 38.0],
        "geometry": "Circle (heaven); 3 tiers, ratios 9:3:1 (sacred 9)"
    },
    "Mogao Caves": {
        "rt60": 4.0,
        "dims": [5.0, 4.0, 3.0],
        "geometry": "Buddhist mandalas; vesica piscis"
    },
    "Longmen Grottoes": {
        "rt60": 3.0,
        "dims": [5.0, 4.0, 3.0],
        "geometry": "Rock-cut φ proportions"
    },
    "Todai-ji Daibutsuden": {
        "rt60": 6.5,
        "dims": [57.0, 50.0, 48.0],
        "geometry": "Golden Buddha; hall ratios 6:5"
    },
    "Horyu-ji": {
        "rt60": 5.0,
        "dims": [32.0, 20.0, 15.0],
        "geometry": "Fibonacci tiers; sqrt(2) base"
    },
    "Kiyomizu-dera": {
        "rt60": 4.0,
        "dims": [13.0, 20.0, 10.0],
        "geometry": "Balcony alignments; 3:4:5"
    },
    "Fushimi Inari": {
        "rt60": 3.0,
        "dims": [50.0, 5.0, 5.0],
        "geometry": "Torii arcs; infinite φ perspective"
    },
    "Parthenon": {
        "rt60": 3.0,
        "dims": [69.5, 30.9, 13.7],
        "geometry": "Facade golden ratio (width:height≈φ); 4:9 base (≈2.25:1)"
    },
    "Temple of Apollo Delphi": {
        "rt60": 4.0,
        "dims": [23.0, 11.0, 9.0],
        "geometry": "Oracle ratios 2:1; mountain phi"
    },
    "Theatre of Epidaurus": {
        "rt60": 1.5,
        "dims": [114.0, 114.0, 10.0],
        "geometry": "Rows φ progression; perfect acoustics"
    },
    "Meteora Monasteries": {
        "rt60": 4.0,
        "dims": [10.0, 8.0, 6.0],
        "geometry": "Cliff mandalas; 3:5 ratios"
    },
    "Hosios Loukas Monastery": {
        "rt60": 5.0,
        "dims": [15.0, 10.0, 10.0],
        "geometry": "Byzantine circles/squares"
    },
    "Pantheon": {
        "rt60": 7.0,
        "dims": [43.3, 43.3, 43.3],
        "geometry": "Perfect sphere; oculus:base=1:6; proportions 1:1:√2"
    },
    "St. Peter’s Basilica": {
        "rt60": 9.0,
        "dims": [136.0, 42.0, 42.0],
        "geometry": "Michelangelo φ in dome; cross plan"
    },
    "Florence Cathedral": {
        "rt60": 8.0,
        "dims": [114.0, 45.0, 45.0],
        "geometry": "Brunelleschi octagon; φ ratios"
    },
    "Basilica di San Marco": {
        "rt60": 6.0,
        "dims": [13.0, 13.0, 13.0],
        "geometry": "Byzantine 5 domes (pentagram?); mosaic diffusion"
    },
    "Basilica di San Francesco": {
        "rt60": 5.0,
        "dims": [80.0, 20.0, 20.0],
        "geometry": "Ratios 4:1; fresco harmony"
    },
    "San Vitale": {
        "rt60": 6.0,
        "dims": [16.0, 16.0, 15.0],
        "geometry": "Octagonal (sacred 8); central dome φ"
    },
    "Chartres Cathedral": {
        "rt60": 6.5,
        "dims": [73.0, 16.0, 37.0],
        "geometry": "Vesica piscis windows; labyrinth φ spiral; proportions 1:φ:φ^2"
    },
    "Notre-Dame de Paris": {
        "rt60": 7.0,
        "dims": [48.0, 12.0, 35.0],
        "geometry": "Rose windows circles; ratios 5:4"
    },
    "Mont-Saint-Michel Abbey": {
        "rt60": 6.0,
        "dims": [50.0, 20.0, 20.0],
        "geometry": "Spire φ curve; island mandala"
    },
    "Sainte-Chapelle": {
        "rt60": 5.0,
        "dims": [36.0, 11.0, 20.0],
        "geometry": "Stained glass ratios 3:2"
    },
    "Sagrada Família": {
        "rt60": 7.0,
        "dims": [90.0, 45.0, 60.0],
        "geometry": "Gaudi hyperbolic paraboloids; tree φ branching"
    },
    "Mezquita-Cathedral": {
        "rt60": 6.0,
        "dims": [180.0, 130.0, 15.0],
        "geometry": "Columns 856 (sacred 8); arches vesica"
    },
    "Seville Cathedral": {
        "rt60": 8.0,
        "dims": [115.0, 76.0, 42.0],
        "geometry": "Largest Gothic; ratios 3:2"
    },
    "Jerónimos Monastery": {
        "rt60": 6.0,
        "dims": [90.0, 30.0, 25.0],
        "geometry": "Manueline knots; φ spirals"
    },
    "Stonehenge": {
        "rt60": 2.0,
        "dims": [33.0, 33.0, 5.0],
        "geometry": "Circles align solstices; Pythagorean triangles; 8x8 grid ratios"
    },
    "Newgrange Passage Tomb": {
        "rt60": 3.0,
        "dims": [19.0, 6.0, 4.0],
        "geometry": "Solstice alignment; sqrt(2) in kerb"
    },
    "Iona Abbey": {
        "rt60": 5.0,
        "dims": [20.0, 10.0, 10.0],
        "geometry": "Celtic knots φ"
    },
    "Rosslyn Chapel": {
        "rt60": 4.0,
        "dims": [21.0, 11.0, 12.0],
        "geometry": "Carvings cubes (Platonic); ratios 2:1"
    },
    "Westminster Abbey": {
        "rt60": 7.0,
        "dims": [156.0, 31.0, 31.0],
        "geometry": "Henry VII chapel fan vault φ"
    },
    "St Paul’s Cathedral": {
        "rt60": 9.0,
        "dims": [111.0, 34.0, 34.0],
        "geometry": "Whisper gallery circle; 3:2 ratios"
    },
    "York Minster": {
        "rt60": 7.5,
        "dims": [80.0, 15.0, 30.0],
        "geometry": "Windows vesica; scale φ"
    },
    "Durham Cathedral": {
        "rt60": 6.5,
        "dims": [145.0, 12.0, 22.0],
        "geometry": "Norman arches; 3:4:5"
    },
    "Cologne Cathedral": {
        "rt60": 8.5,
        "dims": [144.0, 86.0, 43.0],
        "geometry": "Spires 157m (φ progression)"
    },
    "Frauenkirche Dresden": {
        "rt60": 7.0,
        "dims": [26.0, 26.0, 20.0],
        "geometry": "Baroque circle/square"
    },
    "St. Stephen’s Cathedral": {
        "rt60": 6.0,
        "dims": [107.0, 34.0, 28.0],
        "geometry": "Roof tiles mosaic; ratios 3:1"
    },
    "Matthias Church": {
        "rt60": 5.0,
        "dims": [60.0, 23.0, 20.0],
        "geometry": "Neo-Gothic φ tiles"
    },
    "Hagia Sophia": {
        "rt60": 10.5,
        "dims": [55.0, 31.0, 31.0],
        "geometry": "Pendentive geometry; floor plan cross/circle; light cosmology"
    },
    "Blue Mosque": {
        "rt60": 9.0,
        "dims": [43.0, 23.0, 23.0],
        "geometry": "Similar to Hagia; 6 minarets (hexagon)"
    },
    "Chora Church": {
        "rt60": 6.0,
        "dims": [15.0, 10.0, 10.0],
        "geometry": "Byzantine mosaics; vesica"
    },
    "Church of the Holy Sepulchre": {
        "rt60": 5.0,
        "dims": [30.0, 30.0, 20.0],
        "geometry": "Circle (resurrection); multi-room φ"
    },
    "Al-Aqsa Dome of the Rock": {
        "rt60": 4.0,
        "dims": [20.0, 20.0, 15.0],
        "geometry": "Octagon (8); golden dome ratios"
    },
    "Ummayad Mosque": {
        "rt60": 6.0,
        "dims": [157.0, 97.0, 15.0],
        "geometry": "Ratios 1.618 (φ); courtyard reverb"
    },
    "Chichén Itzá El Castillo": {
        "rt60": 1.5,
        "dims": [55.3, 55.3, 30.0],
        "geometry": "365 steps (calendar); chirp echo from stairs (diffraction geometry); equinox serpent shadow"
    },
    "Teotihuacan Feathered Serpent": {
        "rt60": 3.0,
        "dims": [65.0, 65.0, 20.0],
        "geometry": "Pyramid ratios 4:3; serpent alignments"
    },
    "Tulum Temple": {
        "rt60": 2.0,
        "dims": [20.0, 10.0, 5.0],
        "geometry": "Coastal alignments; wave harmonics"
    },
    "Machu Picchu Sun Temple": {
        "rt60": 3.0,
        "dims": [10.0, 10.0, 5.0],
        "geometry": "Intihuatana solar; stone φ fittings"
    },
    "Sacsayhuamán": {
        "rt60": 2.0,
        "dims": [50.0, 20.0, 5.0],
        "geometry": "Polygonal interlock; sqrt(3) angles"
    },
    "Basilica of Guadalupe": {
        "rt60": 6.0,
        "dims": [100.0, 50.0, 20.0],
        "geometry": "Modern oval; Tepeyac hill; modern φ curves"
    },
    "Mission San Carlos Borromeo": {
        "rt60": 4.0,
        "dims": [30.0, 10.0, 10.0],
        "geometry": "Adobe arches; 3:2 ratios"
    },
    "Kiva Spaces Mesa Verde": {
        "rt60": 3.0,
        "dims": [7.0, 7.0, 5.0],
        "geometry": "Circular (unity); underground mandala"
    },
    "Lalibela Rock-Hewn Churches": {
        "rt60": 4.0,
        "dims": [12.0, 10.0, 11.0],
        "geometry": "Cross plans; ratios 1:1 (equality)"
    },
    "Great Mosque of Djenné": {
        "rt60": 5.0,
        "dims": [75.0, 75.0, 10.0],
        "geometry": "Mud-brick spirals; annual renewal (cycle)"
    },
    "Great Zimbabwe Enclosures": {
        "rt60": 3.0,
        "dims": [50.0, 20.0, 5.0],
        "geometry": "Elliptical (vesica-like); stone ratios"
    }
}

# Countries mapping for sites
COUNTRIES = {
    "Egypt": [
        "Great Pyramid King's Chamber", "Great Pyramid Queen's Chamber", "Great Pyramid Grand Gallery",
        "Pyramid of Khafre", "Abu Simbel Temple", "Karnak Temple Hypostyle Hall",
        "Luxor Temple", "Dendera Temple of Hathor", "Philae Temple"
    ],
    "India": [
        "Kailasa Temple Ellora", "Konark Sun Temple", "Brihadeeswarar Temple", "Meenakshi Temple",
        "Golden Temple", "Jagannath Temple", "Kandariya Mahadev", "Kashi Vishwanath",
        "Ramanathaswamy Temple", "Virupaksha Temple", "Ajanta Caves", "Elephanta Caves",
        "Mahabodhi Temple"
    ],
    "Nepal": [
        "Boudhanath Stupa Gallery", "Swayambhunath Caves"
    ],
    "Tibet": [
        "Jokhang Temple", "Potala Palace Chapel", "Tashi Lhunpo Monastery", "Mount Kailash Caves"
    ],
    "Cambodia": [
        "Angkor Wat Outer Galleries", "Angkor Wat Inner Sanctum", "Bayon Temple",
        "Ta Prohm", "Preah Khan"
    ],
    "Indonesia": [
        "Borobudur Central Stupa", "Borobudur Upper Terraces", "Prambanan Temple", "Tanah Lot Shrine"
    ],
    "China": [
        "Temple of Heaven", "Mogao Caves", "Longmen Grottoes"
    ],
    "Japan": [
        "Todai-ji Daibutsuden", "Horyu-ji", "Kiyomizu-dera", "Fushimi Inari"
    ],
    "Greece": [
        "Parthenon", "Temple of Apollo Delphi", "Theatre of Epidaurus"
    ],
    "Italy": [
        "Pantheon", "St. Peter’s Basilica", "Florence Cathedral", "Basilica di San Marco",
        "Basilica di San Francesco", "San Vitale"
    ],
    "France": [
        "Chartres Cathedral", "Notre-Dame de Paris", "Mont-Saint-Michel Abbey", "Sainte-Chapelle"
    ],
    "Spain": [
        "Sagrada Família", "Mezquita-Cathedral", "Seville Cathedral"
    ],
    "Portugal": [
        "Jerónimos Monastery"
    ],
    "United Kingdom": [
        "Stonehenge", "Westminster Abbey", "St Paul’s Cathedral", "York Minster", "Rosslyn Chapel"
    ],
    "Ireland": [
        "Newgrange Passage Tomb", "Iona Abbey"
    ],
    "Germany": [
        "Cologne Cathedral", "Frauenkirche Dresden"
    ],
    "Austria": [
        "St. Stephen’s Cathedral"
    ],
    "Hungary": [
        "Matthias Church"
    ],
    "Turkey": [
        "Hagia Sophia", "Blue Mosque", "Chora Church"
    ],
    "Israel/Palestine": [
        "Church of the Holy Sepulchre", "Al-Aqsa Dome of the Rock"
    ],
    "Syria": [
        "Ummayad Mosque"
    ],
    "Mexico": [
        "Chichén Itzá El Castillo", "Teotihuacan Feathered Serpent", "Tulum Temple",
        "Basilica of Guadalupe"
    ],
    "Peru": [
        "Machu Picchu Sun Temple", "Sacsayhuamán"
    ],
    "United States": [
        "Kiva Spaces Mesa Verde"
    ],
    "Ethiopia": [
        "Lalibela Rock-Hewn Churches"
    ],
    "Mali": [
        "Great Mosque of Djenné"
    ],
    "Zimbabwe": [
        "Great Zimbabwe Enclosures"
    ]
}

# Simple IR generation function for Sanctra
def generate_synthetic_ir(fs=44100, rt60=2.5, length_sec=5, dims=[10.47, 5.235, 5.827], phi=1.618):
    t = np.linspace(0, length_sec, int(fs * length_sec))
    beta = np.log(1000) / rt60
    noise = np.random.normal(0, 1, len(t))
    tail = noise * np.exp(-beta * t)
    # Early reflections
    er_times = np.linspace(0.01, 0.1, 5)
    er = np.zeros(len(t))
    for et in er_times:
        idx = int(et * fs)
        er[idx] = np.random.uniform(0.5, 1.0)
    ir = signal.convolve(er, tail[:len(er)])[:len(t)]
    # Room modes for sacred geometry
    c = 343
    modes = []
    for l in range(3):
        for m in range(3):
            for n in range(3):
                if l == m == n == 0: continue
                f = (c / 2) * np.sqrt((l / dims[0])**2 + (m / dims[1])**2 + (n / dims[2])**2)
                modes.append(f)
    freqs = np.fft.rfftfreq(len(t), 1/fs)
    spec = np.fft.rfft(ir)
    for mode in sorted(modes)[:5]:
        idx = np.argmin(np.abs(freqs - mode))
        spec[idx] *= phi
        for mult in [phi, phi**2]:
            harm = mode * mult
            if harm < fs/2:
                idx = np.argmin(np.abs(freqs - harm))
                spec[idx] *= 1.2
    ir = np.fft.irfft(spec, len(t))
    ir /= np.max(np.abs(ir))
    return ir.tolist()

@app.route('/')
def home():
    return jsonify({"message": "Welcome to Sanctra API! Use /generate-ir, /sites, or /sites-by-country."})

@app.route('/sites', methods=['GET'])
def get_sites():
    return jsonify({"sites": list(SACRED_SITES.keys())})

@app.route('/sites-by-country', methods=['GET'])
def get_sites_by_country():
    return jsonify(COUNTRIES)

@app.route('/generate-ir', methods=['POST'])
def generate_ir():
    data = request.get_json()
    site = data.get('site', 'Great Pyramid King\'s Chamber')
    if site not in SACRED_SITES:
        return jsonify({"error": "Site not found, use /sites to see available sites"}), 400
    rt60 = SACRED_SITES[site]['rt60']
    dims = SACRED_SITES[site]['dims']
    geometry = SACRED_SITES[site]['geometry']
    ir_data = generate_synthetic_ir(rt60=rt60, dims=dims)
    return jsonify({
        "site": site,
        "rt60": rt60,
        "dimensions": dims,
        "geometry": geometry,
        "ir_data": ir_data[:1000]  # Limit response size
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render uses port 10000
    app.run(host='0.0.0.0', port=port, debug=False)
