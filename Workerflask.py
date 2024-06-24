from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import pandas as pd
from ConvertJson import convertData, determine_congestion, get_db_connection
from config import CITYROAD_DELTA
from threading import Timer

app = Flask(__name__)

load_dotenv()
CORS(app, resources={r'*': {'origins': os.getenv("FE_ORIGIN")}})

# 일반 캐시
cache = {}
last_cached_time = datetime.min
cache_interval = timedelta(minutes=5)

# 예측 캐시
prediction_cache = {}

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
    global cache, last_cached_time
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

@app.route('/predict/time', methods=['POST'])
def predict_time():
    global prediction_cache
    try:
        request_data = request.get_json()
        requested_time = datetime.fromisoformat(request_data['time'])

        if requested_time.isoformat() not in prediction_cache:
            cache_data = cache_prediction_data(requested_time)
            if cache_data:
                prediction_cache[requested_time.isoformat()] = cache_data
            else:
                return jsonify({"error": "Prediction data not available"}), 404

        return jsonify({"message": "Prediction data cached successfully"}), 200

    except Exception as e:
        app.logger.error(f"Error processing request: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

@app.route('/predict/area', methods=['POST'])
def predict_area():
    global prediction_cache
    try:
        request_data = request.get_json()
        requested_time = datetime.fromisoformat(request_data['time'])

        # 요청된 시간의 캐시 데이터 가져오기
        if requested_time.isoformat() not in prediction_cache:
            return jsonify({"error": "Prediction data not cached"}), 404

        cache_data = prediction_cache[requested_time.isoformat()]
        include_cityroad = float(request_data['maxX']) - float(request_data['minX']) <= CITYROAD_DELTA
        level = int(request_data.get('zoom', 0))  # MapLevel 값을 int로 변환하고, 기본값을 0으로 설정

        # 필터링 로직 수정
        filtered_data = {
            'items': [item for item in cache_data if
                      float(request_data['minX']) <= float(json.loads(item['geometry'])[0][0]) <= float(request_data['maxX']) and
                      float(request_data['minY']) <= float(json.loads(item['geometry'])[0][1]) <= float(request_data['maxY']) and
                     (include_cityroad or item['road_rank'] != '104' or (
                      item['road_rank'] == '104' and level >= 8))]
        }

        return jsonify(filtered_data)

    except Exception as e:
        app.logger.error(f"Error processing request: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

def cache_prediction_data(requested_time):
    try:
        response_data = []

        conn = get_db_connection()
        db_query = conn.execute('SELECT GEOMETRY, link_id, road_name, road_rank, f_node FROM daejeon_link_wgs84')
        links = db_query.fetchall()

        for link_info in links:
            link_id = link_info['link_id']
            csv_path = f'./predictCSV/{link_id}.csv'

            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path)
                df['datetime'] = pd.to_datetime(df['datetime'])
                matched_row = df[df['datetime'] == requested_time]

                if not matched_row.empty:
                    predicted_speed = matched_row['predicted_speed'].values[0]
                    item = {
                        "id": link_id,
                        "geometry": str(link_info["GEOMETRY"]),
                        "speed": predicted_speed,
                        "road_status": determine_congestion(link_info['road_rank'], predicted_speed),
                        "date": requested_time.isoformat() + "+09:00",
                        "link_Id": link_id,
                        "Node_Id": link_info["f_node"],
                        "road_name": link_info["road_name"] if link_info else "Unknown",
                        "road_rank": link_info["road_rank"] if link_info else "Unknown",
                    }
                    response_data.append(item)
        conn.close()
        return response_data

    except Exception as e:
        app.logger.error(f"Error fetching prediction data: {e}")
        return None

if __name__ == '__main__':
    fetch_and_cache_data()
    app.run(host='0.0.0.0', port=5000, debug=True)
