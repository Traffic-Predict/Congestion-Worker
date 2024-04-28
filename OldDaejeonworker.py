import requests
import json
import time
from datetime import datetime

def callApi():
    api_url = "https://openapi.its.go.kr:9443/trafficInfo"
    api_key = "3ce615607a57401392dac0fa4aa6330d"
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
    if response.status_code == 200:
        return response.json()
    else:
        print("API 요청 실패 : ", response.status_code)
        return None

# totalCount : string -> int
# speed, travelTime : string -> float
# createdDate : string -> datetime
def convertData(data):
    if "body" in data and "items" in data["body"]:
        data["body"]["totalCount"] = int(data["body"]["totalCount"])
        for item in data["body"]["items"]:
            item["speed"] = float(item["speed"])
            item["travelTime"] = float(item["travelTime"])
            try:
                created_date = datetime.strptime(item["createdDate"], "%Y%m%d%H%M%S")
                item["createdDate"] = created_date.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

def saveJson(data, filename):
    convertData(data)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def main():
    while True:
        data = callApi()
        if data:
            print("API 호출 결과:", data)
            timestamp = time.strftime("%Y%m%d%H%M%S")
            filename = f"data_{timestamp}.json"
            saveJson(data, filename)

        # 10분마다 반복
        time.sleep(600)

if __name__ == "__main__":
    main()
