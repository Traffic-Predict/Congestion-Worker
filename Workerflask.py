from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from ConvertJson import convertData
from config import CITYROAD_DELTA
from threading import Timer

app = Flask(__name__)

load_dotenv()
CORS(app, resources={r'*': {'origins': os.getenv("FE_ORIGIN")}})

# 캐시를 저장할 변수와 타임스탬프
cache = None
last_cached_time = datetime.min
cache_interval = timedelta(minutes=5)

def fetch_and_cache_data():
    global cache, last_cached_time
    minX = "127.269182"
    maxX = "127.530568"
    minY = "36.192478"
    maxY = "36.497312"
    data = callApi(minX, maxX, minY, maxY)
    if data:
        cache = convertData(data, True)  # 캐시 데이터는 항상 시내도로를 포함하도록 설정
        last_cached_time = datetime.now()
    Timer(300, fetch_and_cache_data).start()  # 5분마다 재실행

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
        raise Exception(f"API Error: {response.status_code}")

@app.route('/main', methods=['POST'])
def index():
    if datetime.now() - last_cached_time > cache_interval:
        fetch_and_cache_data()

    if cache:
        request_data = request.get_json()
        include_cityroad = float(request_data['maxX']) - float(request_data['minX']) <= CITYROAD_DELTA
        level = int(request_data.get('zoom', 0))  # MapLevel 값을 int로 변환하고, 기본값을 0으로 설정
        # 필터링 로직 수정
        filtered_data = {
            'items': [item for item in cache['items'] if
                      float(request_data['minX']) <= float(json.loads(item['geometry'])[0][0]) <= float(request_data['maxX']) and
                      float(request_data['minY']) <= float(json.loads(item['geometry'])[0][1]) <= float(request_data['maxY']) and
                     (include_cityroad or item['road_rank'] != '104' or (
                      item['road_rank'] == '104' and level >= 8))]

        }
        return jsonify(filtered_data)
    else:
        return jsonify({"error": "API 요청 실패"})

if __name__ == '__main__':
    fetch_and_cache_data()
    app.run(host='0.0.0.0', port=5000, debug=True)
