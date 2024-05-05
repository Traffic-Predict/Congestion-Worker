from datetime import datetime
import sqlite3

def determine_congestion(road_rank, speed):
    congestion_levels = {
        '101': {'congested': 40, 'slow': 80},  # 고속 도로
        '102': {'congested': 30, 'slow': 60},  # 자동차 전용도로
        '103': {'congested': 20, 'slow': 40},  # 일반 국도
        '104': {'congested': 15, 'slow': 30},  # 시내 도로
    }
    if road_rank in congestion_levels:
        if speed <= congestion_levels[road_rank]['congested']:
            return 3
        elif speed <= congestion_levels[road_rank]['slow']:
            return 2
        else:
            return 1
    return 'unknown'

def get_db_connection():
    conn = sqlite3.connect('daejeon_links.sqlite')
    conn.row_factory = sqlite3.Row
    return conn

def convertData(data, include_cityroad=True, start_id=1):
    new_data = {"items": []}
    current_id = start_id
    conn = get_db_connection()
    if "body" in data and "items" in data["body"]:
        for item in data["body"]["items"]:
            created_date = datetime.strptime(item["createdDate"], "%Y%m%d%H%M%S")
            iso_date = created_date.isoformat() + "+09:00"  # KST 기준으로 +09:00 추가
            link_id = int(item["linkId"])
            db_query = conn.execute('SELECT link_id, road_name, road_rank FROM daejeon_link WHERE link_id = ?',
                                    (link_id,))

            link_info = db_query.fetchone()
            if not link_info or link_info['road_rank'] in ('105', '106', '107'): # 지방도는 실시간 교통 예측서 제외
                continue
            if not include_cityroad and link_info['road_rank'] == '104': # 지도 범위에 따라 시내도로 제외
                continue
            road_status = determine_congestion(link_info['road_rank'], float(item["speed"]))
            converted_item = {
                "id": current_id,
                "speed": float(item["speed"]),
                "road_status":road_status,
                "date": iso_date,
                #"time": datetime.strptime(item["createdDate"], "%Y%m%d%H%M%S").hour * 60 + int(
                #    datetime.strptime(item["createdDate"], "%Y%m%d%H%M%S").minute / 10) * 10,
                "link_Id": link_id,
                "Node_Id": int(item["startNodeId"]),
                "road_name": link_info["road_name"] if link_info else "Unknown",
                "road_rank": link_info["road_rank"] if link_info else "Unknown",
            }
            new_data["items"].append(converted_item)
            current_id += 1
    conn.close()
    return new_data
