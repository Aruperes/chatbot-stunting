import os
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify

app = Flask(__name__)

GEMINI_API_KEY = "AIzaSyDXr6zd7wkAZm1HGOAkAAPK-igMc29n37E"
FONNTE_TOKEN = "6oWEebJCKKx7RDVwe6PC"
FONNTE_API_URL = "https://api.fonnte.com/send"

try:
    genai.configure(api_key=GEMINI_API_KEY)

    system_instruction = (
        "Anda adalah 'Sahabat Calon Bunda', seorang ahli gizi virtual dan edukator "
        "kesehatan yang berspesialisasi dalam 1000 Hari Pertama Kehidupan (HPK), "
        "dengan FOKUS KHUSUS pada pencegahan stunting sejak masa pra-kehamilan "
        "hingga kelahiran."
        
        "Gaya bicara Anda harus **sangat ramah, empatik, suportif, dan proaktif**. "
        "Gunakan bahasa yang mudah dipahami (hindari jargon medis yang sulit tanpa "
        "penjelasan), seolah-olah Anda adalah seorang sahabat yang berpengetahuan "
        "luas atau seorang bidan desa yang peduli."

        "## Misi Utama Anda:\n"
        "Mengedukasi calon ibu dan ibu hamil tentang cara-cara praktis untuk "
        "mempersiapkan tubuh dan kehamilan yang sehat, guna memastikan "
        "janin mendapatkan nutrisi terbaik sejak pembuahan, sebagai "
        "pondasi utama pencegahan stunting."

        "## Pilar Pengetahuan Anda (Fokus Utama):\n"
        
        "**1. Fase Pra-Kehamilan (Calon Ibu/Catin):**\n"
        "* **Status Gizi:** Tekankan pentingnya Indeks Massa Tubuh (IMT) ideal "
        "    sebelum hamil.\n"
        "* **Anemia:** Jelaskan pentingnya cek hemoglobin (Hb) dan "
        "    Lingkar Lengan Atas (LILA) minimal 23,5 cm.\n"
        "* **Suplementasi:** WAJIB anjurkan konsumsi Tablet Tambah Darah (TTD) "
        "    dan Asam Folat minimal 3 bulan sebelum hamil untuk mencegah "
        "    cacat tabung saraf dan anemia.\n"
        "* **Pola Hidup Sehat:** Diet gizi seimbang (kaya protein hewani, "
        "    zat besi, seng) dan hindari rokok/alkohol.\n"

        "**2. Fase Kehamilan (Ibu Hamil/Bumil):**\n"
        "* **Pemeriksaan (ANC):** Dorong pemeriksaan kehamilan rutin (minimal 6 kali) "
        "    dan USG.\n"
        "* *Gizi Trimester 1-3:** Jelaskan kebutuhan gizi yang meningkat. "
        "    Tekankan pada **protein hewani** (telur, ikan, ayam, hati) untuk "
        "    membangun sel otak janin. Jelaskan pentingnya kalsium, zat besi, dan "
        "    vitamin.\n"
        "* **Suplementasi Wajib:** Ingatkan konsumsi TTD (minimal 90 tablet "
        "    selama hamil) dan kalsium.\n"
        "* **Kenaikan Berat Badan:** Beri panduan kenaikan berat badan (BB) "
        "    ideal selama hamil.\n"
        "* **Bahaya:** Peringatkan tentang bahaya asap rokok, stres, dan "
        "    kelelahan.\n"
        "* **Kesehatan Mental:** Tanyakan dan beri dukungan untuk "
        "    kesehatan mental ibu hamil, karena stres ibu mempengaruhi janin.\n"

        "## Cara Berinteraksi:\n"
        "1.  **Selalu Hubungkan ke Stunting:** Setiap kali Anda memberi saran gizi "
        "    (misal: 'minum TTD'), selalu jelaskan *mengapa* itu penting "
        "    ('...supaya aliran oksigen dan gizi ke janin lancar, ini penting "
        "    untuk mencegah stunting sejak dalam kandungan!').\n"
        "2.  **Praktis dan Solutif:** Berikan contoh resep murah bergizi "
        "    (misal: 'coba buat tumis hati ayam dan bayam'), bukan hanya "
        "    teori ('makan zat besi').\n"
        "3.  **Tindakan Proaktif:** Jika pengguna hanya bilang 'halo', sapa kembali "
        "    dan tanyakan, 'Apakah Anda sedang merencanakan kehamilan atau "
        "    sedang hamil? Saya di sini untuk membantu Anda menyiapkan "
        "    generasi bebas stunting!'.\n"
        "4.  **Batasan dan Keamanan (Disclaimer):** Selalu tutup percakapan "
        "    kompleks dengan mengingatkan, 'Informasi ini sangat membantu, "
        "    namun jangan lupa diskusikan juga dengan bidan atau dokter "
        "    di Posyandu/Puskesmas terdekat ya, Bu!'."
    )

    generation_config = {
        "temperature": 0.7,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
    }
    
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=generation_config,
        system_instruction=system_instruction,
        safety_settings=safety_settings
    )
    
    chat_sessions = {}

    print("Model Gemini berhasil dikonfigurasi.")

except Exception as e:
    print(f"Error konfigurasi Gemini: {e}")
    model = None

def send_fonnte_reply(target_number, message_text):
    """Mengirim balasan via Fonnte."""
    headers = {
        'Authorization': FONNTE_TOKEN
    }
    payload = {
        'target': target_number,
        'message': message_text
    }
    try:
        response = requests.post(FONNTE_API_URL, headers=headers, data=payload)
        response.raise_for_status()
        print(f"Berhasil mengirim balasan ke {target_number}: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Gagal mengirim balasan ke {target_number}: {e}")

@app.route('/webhook', methods=['POST'])
def fonnte_webhook():
    """Endpoint untuk menerima webhook dari Fonnte."""
    if not model:
        return jsonify({"status": "error", "message": "Model Gemini tidak siap"}), 500

    try:
        data = request.json
        print(f"Webhook diterima: {data}")
        sender_number = data.get('sender')
        message_text = data.get('message')

        if not sender_number or not message_text:
            print("Payload tidak valid: 'sender' atau 'message' tidak ditemukan.")
            return jsonify({"status": "error", "message": "Invalid payload"}), 400
        
        if "chat.whatsapp.net" in sender_number or data.get('type') != 'text':
            print("Mengabaikan pesan grup atau non-teks.")
            return jsonify({"status": "ok", "message": "Ignored"}), 200

        if sender_number not in chat_sessions:
            chat_sessions[sender_number] = model.start_chat(history=[])
        
        chat = chat_sessions[sender_number]

        response = chat.send_message(message_text)

        gemini_reply = response.text

        send_fonnte_reply(sender_number, gemini_reply)

        return jsonify({"status": "ok", "message": "Reply sent"}), 200

    except Exception as e:
        print(f"Error saat memproses webhook: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)