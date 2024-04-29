from flask import Flask, jsonify, request
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)

def callApi(minX, maxX, minY, maxY):
    api_url = "https://openapi.its.go.kr:9443/trafficInfo"
    api_key = os.environ.get("API_KEY")
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
    if "body" in data and "items" in data["body"]:
        for item in data["body"]["items"]:
            converted_item = {
                "id": current_id,
                "speed": float(item["speed"]),
                "date": datetime.strptime(item["createdDate"], "%Y%m%d%H%M%S").strftime("%Y/%m/%d"),
                "time": datetime.strptime(item["createdDate"], "%Y%m%d%H%M%S").hour * 60 + int(datetime.strptime(item["createdDate"], "%Y%m%d%H%M%S").minute /10)*10,
                "link_Id": int(item["linkId"]),
                "Node_Id": int(item["startNodeId"])
            }
            new_data["items"].append(converted_item)
            current_id += 1
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
    app.run(host='0.0.0.0', port=80, debug=True)
