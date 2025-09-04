from flask import Flask, jsonify, request
import numpy as np
import scipy.signal as signal
import os

app = Flask(__name__)

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
    return jsonify({"message": "Welcome to Sanctra API! Use /generate-ir to get IR data."})

@app.route('/generate-ir', methods=['POST'])
def generate_ir():
    data = request.get_json()
    site = data.get('site', 'Great Pyramid King\'s Chamber')
    rt60 = float(data.get('rt60', 2.5))
    dims = data.get('dims', [10.47, 5.235, 5.827])
    ir_data = generate_synthetic_ir(rt60=rt60, dims=dims)
    return jsonify({
        "site": site,
        "rt60": rt60,
        "dimensions": dims,
        "ir_data": ir_data[:1000]  # Limit response size
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Render uses port 10000
    app.run(host='0.0.0.0', port=port, debug=False)
