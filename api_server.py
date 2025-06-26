from flask import Flask, request, jsonify, render_template_string
import random
import string
import hashlib

app = Flask(__name__)

last_decrypted = ''
last_matrix = []
last_seed = ''
known_seeds = {}  # {hash: seed}


def generate_polybius_square(seed=None):
    alphabet = list(string.ascii_uppercase.replace('J', ''))
    if seed:
        random.seed(seed)
    random.shuffle(alphabet)
    return [alphabet[i:i + 5] for i in range(0, 25, 5)]


def decrypt_message(cipher_text, square):
    decrypted = ''
    cipher_text = cipher_text.replace(' ', '')
    for i in range(0, len(cipher_text), 2):
        row = int(cipher_text[i]) - 1
        col = int(cipher_text[i + 1]) - 1
        decrypted += square[row][col]
    return decrypted


@app.route('/')
def home():
    return render_template_string("""
    <html><head><title>Server Status</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background-color: #0d1117;
            color: #c9d1d9;
            text-align: center;
            padding: 40px;
        }
        h2 { color: #ff5555; }
        a { color: #58a6ff; text-decoration: none; }
    </style></head>
    <body>
        <h2>🛡️ Server is Running (Decryption Only)</h2>
        <p>Visit <a href='/latest'>/latest</a> to view decrypted result</p>
    </body></html>
    """)


@app.route('/register_seed', methods=['POST'])
def register_seed():
    data = request.get_json()
    seed = data.get('seed')
    if not seed:
        return jsonify({'error': 'Seed is required'}), 400
    seed_hash = hashlib.sha256(seed.encode()).hexdigest()
    known_seeds[seed_hash] = seed
    return jsonify({'status': 'Seed registered', 'hash': seed_hash})


@app.route('/decrypt', methods=['POST'])
def decrypt():
    global last_decrypted, last_matrix, last_seed
    data = request.get_json()
    seed_hash = data.get('seed_hash')
    cipher = data.get('cipher')

    if not seed_hash or not cipher:
        return jsonify({'error': 'Missing hash or cipher'}), 400

    seed = known_seeds.get(seed_hash)
    if not seed:
        return jsonify({'error': 'Seed hash not recognized'}), 403

    last_seed = seed
    last_matrix = generate_polybius_square(seed)
    last_decrypted = decrypt_message(cipher, last_matrix)

    return jsonify({
        'decrypted': last_decrypted,
        'last_seed': last_seed
    })


@app.route('/latest')
def latest():
    seed_hash = hashlib.sha256(last_seed.encode()).hexdigest() if last_seed else ''
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🛡️ Server Dashboard </title>
        <meta http-equiv="refresh" content="2">
        <style>
            body {
                font-family: 'Segoe UI', sans-serif;
                background-color: #0d1117;
                color: #c9d1d9;
                text-align: center;
                padding: 40px;
            }
            h2 {
                color: #58a6ff;
                margin-bottom: 10px;
            }
            .info-box {
                background-color: #161b22;
                border: 1px solid #30363d;
                padding: 20px;
                margin: 15px auto;
                width: 70%;
                border-radius: 8px;
                text-align: left;
            }
            .info-box strong {
                color: #c9d1d9;
            }
            .highlight {
                color: #f7768e;
            }
            table {
                margin: 20px auto;
                border-collapse: collapse;
                background-color: #161b22;
                border: 1px solid #30363d;
            }
            th, td {
                border: 1px solid #30363d;
                padding: 12px;
                min-width: 40px;
                font-size: 16px;
            }
            .result {
                font-size: 20px;
                font-weight: bold;
                margin-top: 25px;
                color: #9ece6a;
            }
        </style>
    </head>
    <body>
        <h2>Decryption (Server Side) </h2>

        <div class="info-box">
            <p><strong>Seed Hash:</strong> <span class="highlight">{{ seed_hash }}</span></p>
            <p><strong>Plain Seed:</strong> <span class="highlight">{{ last_seed }}</span></p>
        </div>

        <h3 style="color:#7dcfff;">🧮 Polybius Square Matrix</h3>
        {% if matrix %}
            <table>
                {% for row in matrix %}
                    <tr>
                        {% for cell in row %}
                            <td>{{ cell }}</td>
                        {% endfor %}
                    </tr>
                {% endfor %}
            </table>
        {% else %}
            <p><i>No matrix available yet.</i></p>
        {% endif %}

        <div class='result'>
            🔓 Decrypted Message: {{ decrypted }}
        </div>
    </body>
    </html>
    """, matrix=last_matrix, decrypted=last_decrypted, seed_hash=seed_hash, last_seed=last_seed)


if __name__ == "__main__":
    from os import environ
    app.run(host="0.0.0.0", port=int(environ.get("PORT", 5000)))
