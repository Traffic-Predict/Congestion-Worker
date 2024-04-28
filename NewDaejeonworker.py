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


def convertData(data, start_id=1):
    new_data = {
        "items": []
    }
    current_id = start_id  # ID를 start_id에서 시작합니다.

    if "body" in data and "items" in data["body"]:
        for item in data["body"]["items"]:
            converted_item = {}
            converted_item["id"] = current_id  # 매 아이템마다 ID를 1씩 증가
            converted_item["speed"] = float(item["speed"])
            try:
                created_date = datetime.strptime(item["createdDate"], "%Y%m%d%H%M%S")
                converted_item["date"] = created_date.strftime("%Y/%m/%d")
                converted_item["time"] = created_date.hour * 60 + int(created_date.minute /10)*10
                converted_item["link_Id"] = int(item["linkId"])
                converted_item["Node_Id"]=int(item["startNodeId"])
                new_data["items"].append(converted_item)
                current_id += 1  # 다음 아이템을 위해 ID 증가
            except ValueError as e:
                print(f"Date conversion error for {item['createdDate']}: {e}")

    return new_data

def saveJson(data, filename, start_id=1):
    converted_data = convertData(data, start_id)
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(converted_data, f, ensure_ascii=False, indent=4)

def main():
    last_id = 1  # 시작 ID를 1로 설정
    while True:
        data = callApi()
        if data:
            print("API 호출 결과:", data)
            timestamp = time.strftime("%Y%m%d%H%M%S")
            filename = f"transformed_data_{timestamp}.json"
            saveJson(data, filename, last_id)
            last_id += len(data.get("body", {}).get("items", []))  # 저장된 아이템 수만큼 ID를 증가시킵니다.

        # 10분마다 반복
        time.sleep(600)

if __name__ == "__main__":
    main()
