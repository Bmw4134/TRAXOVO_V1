
from flask import Flask, jsonify
from qq_intelligence import qq_intelligence

app = Flask(__name__)

@app.route('/api/all-intelligence')
def all_intelligence():
    return jsonify(qq_intelligence.get_all_intelligence())

@app.route('/api/quantum-consciousness')
def quantum_consciousness():
    return jsonify(qq_intelligence.get_consciousness_metrics())

@app.route('/api/asi-excellence')
def asi_excellence():
    return jsonify(qq_intelligence.get_asi_metrics())

@app.route('/api/gauge-assets')
def gauge_assets():
    return jsonify(qq_intelligence.get_gauge_metrics())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
