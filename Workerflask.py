from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from dotenv import load_dotenv
from ConvertJson import *
import os

app = Flask(__name__)

load_dotenv()

CORS(app, resources={r'*': {'origins': os.getenv("FE_ORIGIN")}})

'''
대전 지역 대략적인 위경도 범위
       "minX": "127.269182",
        "maxX": "127.530568",
        "minY": "36.192478 ",
        "maxY": "36.497312",
'''

def callApi(minX, maxX, minY, maxY):
    api_url = "https://openapi.its.go.kr:9443/trafficInfo"
    api_key = os.getenv("ITS_API_KEY")
    params = {
        "apiKey": api_key,
        "type": "all",
        "drcType": "all",
        "minX": minX,
        "maxX": maxX,
        "minY": minY,
        "maxY": maxY,
        "getType": "json"
    }
    response = requests.get(api_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"{response.status_code}")

@app.route('/main', methods=['POST'])
def index():
    request_data = request.get_json()
    minX = request_data.get('minX')
    maxX = request_data.get('maxX')
    minY = request_data.get('minY')
    maxY = request_data.get('maxY')
    data = callApi(minX, maxX, minY, maxY)
    if data:
        converted_data = convertData(data)
        return jsonify(converted_data)
    else:
        return jsonify({"error": "API 요청 실패"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
