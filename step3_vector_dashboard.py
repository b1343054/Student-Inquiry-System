import chromadb

def get_records_from_chroma():
    """从向量库读取所有表结构记录"""
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_collection(name="db_schema_collection")
    results = collection.get()
    
    records = {}
    for doc, meta in zip(results["documents"], results["metadatas"]):
        table_name = meta["table_name"]
        records[table_name] = doc
    return records

def show_all_records(records):
    """展示所有向量库记录"""
    print("\n📚 向量库中所有表结构记录：")
    for table_name, content in records.items():
        print(f"\n===== {table_name} =====")
        print(content)

def query_direct(records):
    """繁简体关键词查询功能（修正缩进版）"""
    print("\n🔍 表结构查询功能")
    print("输入 'exit' 可退出查询")

    while True:
        query_text = input("\n请输入你的查询问题：")
        if query_text.lower() == "exit":
            print("👋 退出查询功能")
            break

        found = False

        # 简体+繁体关键词映射
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

        # 匹配关键词
        target_tables = []
        for keyword, table in keyword_map.items():
            if keyword in query_text:
                target_tables.append(table)
        target_tables = list(set(target_tables))

        # 输出结果
        for table in target_tables:
            print(f"\n✅ 查询结果：")
            print(f"表名：{table}")
            print(f"内容：\n{records[table]}")
            found = True

        if not found:
            print("❌ 未找到匹配的表，请换个关键词试试（比如 学生/問卷/答題）")

def student():
    """主菜单"""
    records = get_records_from_chroma()

    while True:
        print("\n=== 向量库管理工具 ===")
        print("1. 展示所有记录")
        print("2. 查询表结构")
        print("3. 退出程序")

        choice = input("请输入选项数字：")
        if choice == "1":
            show_all_records(records)
        elif choice == "2":
            query_direct(records)
        elif choice == "3":
            print("👋 退出程序")
            break
        else:
            print("❌ 无效选项，请输入 1/2/3")

if __name__ == "__student__":
    student()