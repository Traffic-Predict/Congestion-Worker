from flask import Flask, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

def callApi():
    api_url = "https://openapi.its.go.kr:9443/trafficInfo"
    api_key = ""
    params = {
        "apiKey": api_key,
        "type": "all",
        "drcType": "all",
        "minX": "127.269182",
        "maxX": "127.530568",
        "minY": "36.192478 ",
        "maxY": "36.497312",
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

@app.route('/')
def index():
    data = callApi()
    if data:
        converted_data = convertData(data)
        return jsonify(converted_data)
    else:
        return jsonify({"error": "API 요청 실패"})

if __name__ == '__main__':
    app.run(debug=True)
