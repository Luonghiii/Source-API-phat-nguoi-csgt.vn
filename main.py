from flask import Flask, request

app = Flask(__name__)

@app.route('/tra-cuu', methods=['GET'])
def tra_cuu():
    bienso = request.args.get('bienso')
    loaixe = request.args.get('loaixe')
    apicaptcha = request.args.get('apicaptcha')
    if not all([bienso, loaixe, apicaptcha]):
        return {"error": "Thiếu tham số"}
    return kiemtra_bienso(bienso, loaixe, apicaptcha)

if __name__ == '__main__':
    app.run(port=5000)
