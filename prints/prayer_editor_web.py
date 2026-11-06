#!/usr/bin/env python3
"""
prayer_editor_web.py — Minimal visual prayer card editor.

Features:
- Type devanagari (Tiro Devanagari Sanskrit) and English (Cormorant Garamond)
- Adjust font sizes with sliders
- Preview on POSTCARD 4×6″ vertical (1200×1800 px @ 300 DPI)
- Save spec JSON
- Render PNG

Run: python3 prints/prayer_editor_web.py
Then open http://127.0.0.1:3769/editor
"""
import json, os, sys
from pathlib import Path
from flask import Flask, render_template_string, request, send_file, jsonify

# --- Config ---
ROOT = Path(__file__).parent.parent
PRAYERS_DIR = ROOT / "prints" / "prayers"
SPECS = sorted(PRAYERS_DIR.glob("*.json"))

# Available fonts (already on this system)
TIO = "/root/.fonts/TiroDevanagariSanskrit-Regular.ttf"
COR = "/root/.fonts/CormorantGaramond[wght].ttf"

app = Flask(__name__)

# Default spec
current_spec = {
    "id": "newprayer",
    "title": "New Prayer from Lakshmanjoo",
    "source": "mined from Lakshmanjoo Shivastotravali corpus",
    "dev_sd": 70,
    "en_se": 52,
    "stanzas": [
        {
            "dev": "न ध्यायतो न जपतः स्याद् यस्याविधिपूर्वकम् / एवम् एव शिवभासस् तं नुमो भक्तिशालिनम्",
            "en": "I bow to that devotee who is glorified with the devotion of Lord Shiva and to whom the appearance of Lord Shiva takes place without conducting meditation or recitation of any kind."
        }
    ]
}

load_current_spec = lambda: None
save_current_spec = lambda: None

def load_current_spec():
    global current_spec
    # Try to load first available spec, or use default
    if SPECS:
        try:
            text = SPECS[0].read_text()
            current_spec = json.loads(text)
            if "dev_sd" not in current_spec:
                current_spec["dev_sd"] = 70
            if "en_se" not in current_spec:
                current_spec["en_se"] = 52
        except:
            pass

def save_current_spec():
    if SPECS:
        SPECS[0].write_text(json.dumps(current_spec, indent=2, ensure_ascii=False))

load_current_spec()

@app.route("/")
@app.route("/editor")
def editor():
    load_current_spec()
    return render_template_string("""
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Prayer Card Editor — Lakshmanjoo Editions</title>
    <style>
        body {font: 14px system-ui, -apple-system, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; background: #faf9f7; color: #17140f;}
        .container {background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 18px rgba(0,0,0,.12);}
        h1 {font-weight: 600; margin-top: 0; border-bottom: 2px solid #e0e0e0; padding-bottom: 0.5rem;}
        .spec-info {background: #f8f9fa; padding: 1rem; border-radius: 4; margin: 1rem 0;}
        .control {margin: 1rem 0;}
        label {display: block; font-weight: 500; margin-bottom: 0.3rem;}
        input[type=number], input[type=text] {width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; margin: 0.3rem 0;}
        .preview {border: 1px solid #e0e0e0; padding: 2rem; min-height: 300px; display: flex; align-items: center; justify-content: center; background: #fff; margin: 1rem 0; position: relative;}
        .dev-text {font-family: 'Tiro Devanagari Sanskrit', serif; font-size: {{dev_sd}}pt; color: #17140f; line-height: 1.4; }
        .en-text {font-family: 'Cormorant Garamond', serif; font-size: {{en_se}}pt; color: #17140f; line-height: 1.4; }
        .status {color: #666; font-size: 0.9rem; margin-top: 1rem;}
        .btn {padding: 0.6rem 1.2rem; background: #0066cc; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9rem; margin: 0.2rem;}
        .btn-secondary {background: #666; margin-left: 0.5rem;}
        .ratio-info {font-size: 0.8rem; color: #666; margin-top: 0.5rem; align-self: flex-end;}
        .stanza {margin: 1rem 0; padding: 0.5rem; border: 1px solid #eee; border-radius: 4px;}
        .stanza-dev {font-family: 'Tiro Devanagari Sanskrit', serif; font-size: {{dev_sd}}pt; color: #17140f; margin: 0.2rem 0;}
        .stanza-en {font-family: 'Cormorant Garamond', serif; font-size: {{en_se}}pt; color: #17140f; margin: 0.2rem 0;}
    </style>
    <script>
        function updatePreview() {
            const dev_sd = parseInt(document.getElementById('dev_sd').value);
            const en_se = parseInt(document.getElementById('en_se').value);
            document.getElementById('preview-dev').style.fontSize = dev_sd + 'pt';
            document.getElementById('preview-en').style.fontSize = en_se + 'pt';
            document.getElementById('dev_sd_val').textContent = dev_sd;
            document.getElementById('en_se_val').textContent = en_se;
        }
        
        function addStanza() {
            const container = document.getElementById('stanzas');
            const i = container.children.length;
            const div = document.createElement('div');
            div.className = 'stanza';
            div.innerHTML = `
                <h3>Stanza ${i+1}</h3>
                <div class="control">
                    <label>Devanagari</label>
                    <textarea id="dev${i}" rows="2" placeholder="न ध्यायतो न जपतः स्याद् यस्याविधिपूर्वकम् / एवम् एव शिवभासस्"></textarea>
                </div>
                <div class="control">
                    <label>English</label>
                    <textarea id="en${i}" rows="2" placeholder="I bow to that devotee who is glorified..."></textarea>
                </div>
                <button class="btn btn-secondary" onclick="removeStanza(${i})">Remove</button>
            `;
            container.appendChild(div);
        }
        
        function removeStanza(i) {
            const container = document.getElementById('stanzas');
            container.removeChild(container.children[i]);
        }
        
        function saveSpec() {
            const spec = {
                id: document.getElementById('spec_id').value || 'newprayer',
                title: document.getElementById('spec_title').value || 'Lakshmanjoo Prayer',
                source: document.getElementById('spec_source').value || 'mined from Lakshmanjoo Shivastotravali',
                dev_sd: parseInt(document.getElementById('dev_sd').value),
                en_se: parseInt(document.getElementById('en_se').value),
                stanzas: []
            };
            
            const count = container.children.length;
            for (let i = 0; i < count; i++) {
                const dev = document.getElementById('dev' + i).value.trim();
                const en = document.getElementById('en' + i).value.trim();
                if (dev || en) {
                    spec.stanzas.push({
                        dev: dev.split('\\n').filter(l => l.trim()),
                        en: en.split('\\n').filter(l => l.trim())
                    });
                }
            }
            
            fetch('/api/spec', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(spec)
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('status').textContent = data.status ? 'Saved OK' : 'Error: ' + (data.error || '');
            })
            .catch(() => document.getElementById('status').textContent = 'Save failed');
        }
        
        function renderAndDownload() {
            saveSpec();
            document.getElementById('status').textContent = 'Rendering...';
            fetch('/render')
            .then(() => {
                document.getElementById('status').textContent = 'Rendering complete - check download below';
            })
            .catch(() => document.getElementById('status').textContent = 'Render started');
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>Prayer Card Editor — Lakshmanjoo Editions</h1>
        
        <div class="spec-info">
            <strong>Title:</strong> <input type="text" id="spec_title" value="{{ spec.title || 'New Prayer from Lakshmanjoo' }}"><br>
            <strong>Source:</strong> <input type="text" id="spec_source" value="{{ spec.source || 'mined from Lakshmanjoo Shivastotravali corpus' }}"><br>
            <strong>ID:</strong> <input type="text" id="spec_id" value="{{ spec.id || 'newprayer' }}">
        </div>
        
        <div class="control">
            <label>Dev font size (pt)</label>
            <input type="number" id="dev_sd" min="10" max="120" value="{{ spec.dev_sd or 70 }}" oninput="updatePreview()"> 
            <span id="dev_sd_val">{{ spec.dev_sd or 70 }}</span> pts
        </div>
        
        <div class="control">
            <label>Eng font size (pt)</label>
            <input type="number" id="en_se" min="10" max="120" value="{{ spec.en_se or 52 }}" oninput="updatePreview()"> 
            <span id="en_se_val">{{ spec.en_se or 52 }}</span> pts
        </div>
        
        <div class="control">
            <label>Number of stanzas</label>
            <button class="btn" onclick="addStanza()">Add Stanza</button>
            <span id="stanza-count">1 stanza</span>
        </div>
        
        <div id="stanzas">
            {% for i, st in enumerate(spec.stanzas|default([{'dev': '', 'en': ''}])) %}
            <div class="stanza">
                <h3>Stanza {{ i+1 }}</h3>
                <div class="control">
                    <label>Devanagari</label>
                    <textarea id="dev{{ i }}" rows="2" class="stanza-dev">{{ st.dev[0] if st.dev else 'न ध्यायतो न जपतः स्याद् यस्याविधिपूर्वकम् / एवम् एव शिवभासस् तं नुमो भक्तिशालिनम' }}</textarea>
                </div>
                <div class="control">
                    <label>English</label>
                    <textarea id="en{{ i }}" rows="2" class="stanza-en">{{ st.en[0] if st.en else 'I bow to that devotee who is glorified with the devotion of Lord Shiva and to whom the appearance of Lord Shiva takes place without conducting meditation or recitation of any kind.' }}</textarea>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <button class="btn" onclick="addStanya()">Add Stanza</button>
        <button class="btn btn-secondary" onclick="removeStanzaLast()">Remove Last</button>
        
        <div class="preview">
            <div id="preview-dev" class="dev-text" style="font-size: 70pt;">न ध्यायतो न जपतः स्याद् यस्याविधिपूर्वकम् / एवम् एव शिवभासस् तं नुमो भक्तिशालिनम</div>
            <div id="preview-en" class="en-text" style="font-size: 52pt; margin-top: 2rem;">I bow to that devotee who is glorified with the devotion of Lord Shiva and to whom the appearance of Lord Shiva takes place without conducting meditation or recitation of any kind.</div>
            <div class="ratio-info">POSTCARD 4×6″ vertical — 1200×1800 px @ 300 DPI</div>
        </div>
        
        <button class="btn" onclick="renderAndDownload()">Render & Download POSTCARD PNG</button>
        <button class="btn btn-secondary" onclick="saveSpec()">Save Spec JSON</button>
        
        <div id="status" class="status"></div>
    </div>
    
    <script>
        // Initial update
        window.onload = updatePreview;
    </script>
</body>
</html>
""", spec=current_spec)

@app.route("/api/spec", methods=["GET", "POST"])
def api_spec():
    global current_spec
    if request.method == "POST":
        try:
            current_spec = request.get_json()
            save_current_spec()
            return jsonify({"status": "ok", "spec": current_spec})
        except Exception as e:
            return jsonify({"status": "error", "error": str(e)}), 400
    return jsonify({"status": "ok", "spec": current_spec})

@app.route("/render")
def render():
    """Render the current spec to POSTCARD PNG and return it."""
    try:
        import json
        from pathlib import Path
        from PIL import Image, ImageDraw, ImageFont
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
        
        spec = current_spec
        dev_sd = spec.get("dev_sd", 70)
        en_se = spec.get("en_se", 52)
        
        # Build image
        W, H = 1200, 1800
        SAFE = 250
        img = Image.new("RGB", (W, H), (255, 255, 255))
        d = ImageDraw.Draw(img)
        
        fd = ImageFont.truetype(TIO, dev_sd)
        fe = ImageFont.truetype(COR, en_se, 500)
        
        INK = (23, 20, 15)
        max_w, max_h = W - 2 * SAFE, H - 2 * SAFE
        
        # Parse stanzas from spec
        stanzas = spec.get("stanzas", [])
        if not stanzas and "stanza" in request.args:
            # Try to parse from form data
            pass
        
        # Simple rendering: center the text
        # Use first stanza's text if available
        first_dev = spec.get("stanzas", [{}])[0].get("dev", ["न ध्यायतो न जपतः"])[0]
        first_en = spec.get("stanzas", [{}])[0].get("en", ["I bow to that devotee..."])[0]
        
        # Calculate position to center
        d_text = first_dev.split('/')
        e_text = first_en.split('. ')
        
        y = SAFE
        x0 = W / 2
        
        # Write devanagari
        for line in d_text:
            line = line.strip()
            if line:
                d.text((x0 - fd.getlength(line) / 2, y), line, font=fd, fill=INK)
                y += 1.72 * dev_sd
        
        # Write english
        y += 20  # gap
        for sentence in first_en.split('. '):
            sentence = sentence.strip()
            if sentence and not sentence.endswith('.'):
                sentence = sentence + '.'
            if sentence:
                d.text((x0 - fe.getlength(sentence) / 2, y), sentence, font=fe, fill=INK)
                y += 1.60 * en_se
        
        # Save
        out_path = Path("/tmp") / f"{spec.get('id', 'prayer')}_postcard_1200x1800.png"
        img.save(out_path, optimize=True)
        
        return send_file(out_path, mimetype="image/png", download_name=f"{spec.get('id', 'prayer')}_postcard.png")
        
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3769, debug=False)
