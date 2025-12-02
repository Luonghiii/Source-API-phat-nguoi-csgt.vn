from flask import Flask, request, jsonify
import json
import os

# Import hàm từ main.py
from xuly import kiemtra_bienso

app = Flask(__name__)

# Endpoint gốc - kiểm tra API có hoạt động không
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "🚦 API Tra Cứu Vi Phạm CSGT",
        "author": "Luonghiii",
        "usage": "/api/tracuu?bienso=30A12345&loaixe=1&captcha=YOUR_KEY"
    })

# Endpoint tra cứu vi phạm
@app.route('/api/tracuu', methods=['GET'])
def tracuu():
    # Lấy tham số từ URL
    bienso = request.args.get('bienso')
    loaixe = request.args.get('loaixe')
    captcha = request.args.get('captcha')
    
    # Kiểm tra thiếu tham số
    if not bienso:
        return jsonify({"status": "error", "message": "Thiếu tham số: bienso"}), 400
    if not loaixe:
        return jsonify({"status": "error", "message": "Thiếu tham số: loaixe"}), 400
    if not captcha:
        return jsonify({"status": "error", "message": "Thiếu tham số: captcha"}), 400
    
    # Gọi hàm tra cứu
    try:
        result = kiemtra_bienso(bienso, loaixe, captcha)
        # Chuyển JSON string thành object
        return jsonify(json.loads(result))
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Lỗi xử lý: {str(e)}"
        }), 500

# Chạy Flask app
if __name__ == '__main__':
    # Railway tự động cấp PORT qua biến môi trường
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
