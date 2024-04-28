import sqlite3

def query_data(db_path):
    # 데이터베이스 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # SQL 쿼리 실행
    query = "SELECT * FROM daejeon_node_xy"  # daejeon_node_xy 테이블의 모든 데이터를 조회
    cursor.execute(query)

    # 데이터 출력
    rows = cursor.fetchall()
    for row in rows:
        print(row)

    # 연결 종료
    cursor.close()
    conn.close()

def get_table_info(db_path, table_name):
    # 데이터베이스에 연결
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # PRAGMA 명령을 사용하여 테이블 정보 조회
    cursor.execute(f"PRAGMA table_info({table_name})")

    # 조회 결과 출력
    columns = cursor.fetchall()
    print("Column Info:")
    print("ID, Name, Type, Not Null, Default Value, Primary Key")
    for col in columns:
        print(col)

    # 연결 종료
    cursor.close()
    conn.close()

if __name__ == "__main__":
    db_path = 'daejeon_node_xy.sqlite'
    table_name = 'daejeon_node_xy'
    #get_table_info(db_path, table_name)  #테이블 속성 조회
    query_data(db_path) #테이블 데이터 조회
