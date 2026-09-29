# 匯入資料庫連線函式庫
import mysql.connector
from mysql.connector import Error

# 定義函數：讀取三張表的結構並轉為文字
def get_db_schema_text():
    # 指定你專案的三張目標表
    target_tables = ["student", "questionnaire_questions", "qustionnaire_result"]
    # 空列表：用來存放每張表的文字資訊
    schema_texts = []

    # 1. 連線本機 MySQL 資料庫
    try:
        conn = mysql.connector.connect(
            host="localhost",     # 本機資料庫位址
            user="root",          # MySQL 帳號
            password="1234",      # 你的 MySQL 密碼
            database="mobilescreenresearch"  # 你的資料庫名稱
        )

        # 判斷是否連線成功
        if conn.is_connected():
            print("✅ MySQL 資料庫連線成功")
            # 建立游標，用來執行 SQL 語句
            cursor = conn.cursor()

            # 2. 迴圈遍歷每一張表
            for table_name in target_tables:
                # SQL 語句：查詢表的欄位結構
                sql = f"DESCRIBE `{table_name}`;"
                cursor.execute(sql)
                # 取得查詢結果（所有欄位資訊）
                columns = cursor.fetchall()

                # 3. 把資料表結構拼接成一段自然文字（向量化需要文字格式）
                text_content = f"資料表名稱：{table_name}\n"
                text_content += "欄位詳情：\n"

                # 遍歷目前資料表的每一個欄位
                for col in columns:
                    # col 格式：(欄位名, 資料類型, 是否為空, 鍵類型, 預設值, 額外屬性)
                    field_name = col[0]
                    field_type = col[1]
                    key_type = col[3]

                    # 判斷是否為主鍵
                    if key_type == "PRI":
                        key_desc = "該欄位為主鍵"
                    else:
                        key_desc = "該欄位非主鍵"

                    # 拼接單行欄位描述
                    text_content += f"欄位名：{field_name}，資料類型：{field_type}，{key_desc}\n"

                # 把目前資料表的名稱 + 文字 存入列表
                schema_texts.append({
                    "table_name": table_name,
                    "text": text_content
                })

            # 關閉游標、關閉資料庫連線
            cursor.close()
            conn.close()
            return schema_texts

    # 擷取資料庫連線錯誤
    except Error as e:
        print(f"❌ 資料庫連線失敗：{e}")
        return []

# 程式進入點：執行函數
if __name__ == "__student__":
    result = get_db_schema_text()
    # 列印讀取到的文字內容
    for item in result:
        print("----------------------------------------")
        print(item["text"])
