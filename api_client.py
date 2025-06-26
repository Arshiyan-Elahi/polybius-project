from flask import Flask, render_template_string, request, redirect
import random
import string
import hashlib
import requests

app = Flask(__name__)

def generate_polybius_square(seed=None):
    alphabet = list(string.ascii_uppercase.replace('J', ''))
    if seed:
        random.seed(seed)
    random.shuffle(alphabet)
    return [alphabet[i:i + 5] for i in range(0, 25, 5)]

def encrypt_message(text, square):
    text = text.upper().replace('J', 'I')
    encrypted = ''
    for char in text:
        if char in string.ascii_uppercase:
            for row in range(5):
                if char in square[row]:
                    col = square[row].index(char)
                    encrypted += str(row + 1) + str(col + 1) + ' '
                    break
    return encrypted.strip()

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Client Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
            color: #ffffff;
            text-align: center;
            padding: 40px;
            animation: fadeIn 1s ease-in;
        }
        input, button {
            padding: 12px;
            margin: 10px;
            font-size: 16px;
            border-radius: 8px;
            border: none;
            outline: none;
            width: 250px;
            background-color: #1f2937;
            color: #fff;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: 0.3s ease;
        }
        input:focus {
            border: 2px solid #3b82f6;
        }
        button {
            background-color: #10b981;
            cursor: pointer;
        }
        button:hover {
            background-color: #059669;
            transform: scale(1.05);
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            background-color: #111827;
            border-left: 5px solid #10b981;
            border-radius: 10px;
            font-size: 18px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.4);
            display: inline-block;
            animation: fadeIn 0.7s ease-in-out;
        }
        table {
            margin: 20px auto;
            border-collapse: collapse;
            background-color: #1f2937;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        th, td {
            border: 1px solid #374151;
            padding: 12px 16px;
            color: #e5e7eb;
        }
        th {
            background-color: #111827;
        }
        h2 {
            color: #3b82f6;
            font-size: 32px;
            margin-bottom: 20px;
        }
        h3 {
            color: #fbbf24;
        }
        @keyframes fadeIn {
            from {opacity: 0;}
            to {opacity: 1;}
        }
    </style>
</head>
<body>
    <h2>Encryption (Client Side)</h2>
    <form method="POST">
        <input type="text" name="seed" placeholder="Enter Seed " required>
        <input type="text" name="message" placeholder="Enter Message " required>
        <br>
        <button type="submit">Encrypt & Send</button>
    </form>

    {% if matrix %}
    <h3>Polybius Square Matrix</h3>
    <table>
        <tr><th></th>{% for col in range(1, 6) %}<th>{{ col }}</th>{% endfor %}</tr>
        {% for i in range(5) %}
        <tr><th>{{ i+1 }}</th>{% for j in range(5) %}<td>{{ matrix[i][j] }}</td>{% endfor %}</tr>
        {% endfor %}
    </table>
    {% endif %}

    {% if encrypted %}
    <div class="result">
        <strong>🔒 Encrypted by Client:</strong> {{ encrypted }}
    </div>
    {% endif %}

    {% if decrypted %}
    <div class="result">
        <strong>🔓 Decrypted by Server:</strong> {{ decrypted }}
    </div>
    {% endif %}
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    encrypted = decrypted = ''
    matrix = []

    if request.method == 'POST':
        seed = request.form['seed']
        message = request.form['message']
        matrix = generate_polybius_square(seed)
        encrypted = encrypt_message(message, matrix)

        # Generate SHA-256 hash of the seed
        seed_hash = hashlib.sha256(seed.encode()).hexdigest()

        try:
            # Register the seed hash (optional — can be skipped if pre-registered)
            requests.post('https://polybius-project.onrender.com/register_seed', json={'seed': seed})

            # Send cipher + seed_hash to server for decryption
            res = requests.post('https://polybius-project.onrender.com/decrypt', json={
                'seed_hash': seed_hash,
                'cipher': encrypted
            })
            decrypted = res.json().get('decrypted', 'N/A')
            return redirect("https://polybius-project.onrender.com/latest")

        except Exception as e:
            decrypted = f"❌ Server error: {e}"

    return render_template_string(html_template, encrypted=encrypted, decrypted=decrypted, matrix=matrix)

if __name__ == "__main__":
    from os import environ
    app.run(host="0.0.0.0", port=int(environ.get("PORT", 5000)))

