import chromadb

def get_records_from_chroma():
    """從向量庫讀取所有資料表結構紀錄"""
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name="db_schema_collection")
    results = collection.get()
    
    records = {}
    for doc, meta in zip(results["documents"], results["metadatas"]):
        table_name = meta["table_name"]
        records[table_name] = doc
    return records

def show_all_records(records):
    """展示所有向量庫紀錄"""
    print("\n📚 向量庫中所有資料表結構紀錄：")
    for table_name, content in records.items():
        print(f"\n===== {table_name} =====")
        print(content)

def query_direct(records):
    """繁簡體關鍵字查詢功能（修正縮排版）"""
    print("\n🔍 資料表結構查詢功能")
    print("輸入 'exit' 可退出查詢")

    while True:
        query_text = input("\n請輸入你的查詢問題：")
        if query_text.lower() == "exit":
            print("👋 退出查詢功能")
            break

        found = False

        # 簡體+繁體關鍵字映射
        keyword_map = {
            "学生": "student",
            "學生": "student",
            "基本信息": "student",
            "基本訊息": "student",
            "個人資訊": "student",
            "个人信息": "student",

            "问卷": "questionnaire_questions",
            "問卷": "questionnaire_questions",
            "题目": "questionnaire_questions",
            "題目": "questionnaire_questions",
            "問題": "questionnaire_questions",
            "问题": "questionnaire_questions",

            "答题": "qustionnaire_result",
            "答題": "qustionnaire_result",
            "结果": "qustionnaire_result",
            "結果": "qustionnaire_result",
            "成績": "qustionnaire_result",
            "成绩": "qustionnaire_result"
        }

        # 匹配關鍵字
        target_tables = []
        for keyword, table in keyword_map.items():
            if keyword in query_text:
                target_tables.append(table)
        target_tables = list(set(target_tables))

        # 輸出結果
        for table in target_tables:
            print(f"\n✅ 查詢結果：")
            print(f"資料表名稱：{table}")
            print(f"內容：\n{records[table]}")
            found = True

        if not found:
            print("❌ 未找到匹配的資料表，請換個關鍵字試試（例如 學生/問卷/答題）")

def student():
    """主選單"""
    records = get_records_from_chroma()

    while True:
        print("\n=== 向量庫管理工具 ===")
        print("1. 展示所有紀錄")
        print("2. 查詢資料表結構")
        print("3. 退出程式")

        choice = input("請輸入選項數字：")
        if choice == "1":
            show_all_records(records)
        elif choice == "2":
            query_direct(records)
        elif choice == "3":
            print("👋 退出程式")
            break
        else:
            print("❌ 無效選項，請輸入 1/2/3")

if __name__ == "__student__":
    student()
