from flask import Flask, jsonify, request
import requests
from datetime import datetime
import sqlite3

app = Flask(__name__)

'''
대전 지역 대략적인 위경도 범위
       "minX": "127.269182",
        "maxX": "127.530568",
        "minY": "36.192478 ",
        "maxY": "36.497312",

'''
def get_db_connection():
    conn = sqlite3.connect('daejeon_links.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

def callApi(minX, maxX, minY, maxY):
    api_url = "https://openapi.its.go.kr:9443/trafficInfo"
    api_key = ""
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
    return response.json() if response.status_code == 200 else None

def convertData(data, start_id=1):
    new_data = {"items": []}
    current_id = start_id
    conn = get_db_connection()
    if "body" in data and "items" in data["body"]:
        for item in data["body"]["items"]:
            created_date = datetime.strptime(item["createdDate"], "%Y%m%d%H%M%S")
            iso_date = created_date.isoformat() + "+09:00"  # KST 기준으로 +09:00 추가
            link_id = int(item["linkId"])
            db_query = conn.execute('SELECT link_id, road_name,road_rank,max_spd FROM daejeon_link WHERE link_id = ?', (link_id,))
            link_info = db_query.fetchone()
            converted_item = {
                "id": current_id,
                "speed": float(item["speed"]),
                "date": iso_date,
                "time": datetime.strptime(item["createdDate"], "%Y%m%d%H%M%S").hour * 60 + int(datetime.strptime(item["createdDate"], "%Y%m%d%H%M%S").minute /10)*10,
                "link_Id": link_id,
                "Node_Id": int(item["startNodeId"]),
                "road_name": link_info["road_name"] if link_info else "Unknown",
                "road_rank": link_info["road_rank"]if link_info else "Unknown",
                "max_spd": link_info["max_spd"] if link_info else "Unknown"
            }
            new_data["items"].append(converted_item)
            current_id += 1
    conn.close()
    return new_data

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
