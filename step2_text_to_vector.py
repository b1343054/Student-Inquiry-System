import mysql.connector
from mysql.connector import Error
from sklearn.feature_extraction.text import CountVectorizer
import chromadb

# --------------------------
# 1. 讀取資料庫資料表結構（升級版：包含資料表註釋和欄位註釋）
# --------------------------
def get_db_schema_text():
    target_tables = ["student", "questionnaire_questions", "qustionnaire_result"]
    schema_texts = []

    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="mobilescreenresearch"
        )

        if conn.is_connected():
            print("✅ MySQL 資料庫連線成功")
            cursor = conn.cursor()

            for table_name in target_tables:
                # --- 新增：讀取資料表註釋 ---
                cursor.execute(f"SHOW TABLE STATUS LIKE '{table_name}'")
                table_status = cursor.fetchone()
                table_comment = table_status[17] if table_status else ""

                # --- 改動：用 SHOW FULL COLUMNS 讀取欄位（包含註釋）---
                cursor.execute(f"SHOW FULL COLUMNS FROM `{table_name}`")
                columns = cursor.fetchall()

                # 建構帶註釋的文字
                text_content = f"資料表名稱：{table_name}\n"
                if table_comment:
                    text_content += f"資料表註釋：{table_comment}\n"
                text_content += "欄位詳情：\n"

                for col in columns:
                    field_name = col[0]
                    field_type = col[1]
                    key_type = col[3]
                    field_comment = col[8]  # 第9欄是欄位註釋

                    if key_type == "PRI":
                        key_desc = "該欄位為主鍵"
                    else:
                        key_desc = "該欄位非主鍵"

                    text_content += f"欄位名：{field_name}，資料類型：{field_type}，{key_desc}"
                    if field_comment:
                        text_content += f"，註釋：{field_comment}"
                    text_content += "\n"

                schema_texts.append({
                    "table_name": table_name,
                    "text": text_content
                })

            cursor.close()
            conn.close()
            return schema_texts

    except Error as e:
        print(f"❌ 資料庫連線失敗：{e}")
        return []

# --------------------------
# 2. 簡易向量化（不用改）
# --------------------------
def text_to_vector_simple(texts):
    vectorizer = CountVectorizer()
    vectorizer.fit(texts)
    vectors = vectorizer.transform(texts).toarray()
    return vectors, vectorizer

# --------------------------
# 3. 存入 Chroma 向量庫（不用改）
# --------------------------
def save_to_chroma(schema_texts, vectors):
    client = chromadb.PersistentClient(path="./chroma_db")
    collection = client.get_or_create_collection(name="db_schema_collection")

    for idx, item in enumerate(schema_texts):
        table_name = item["table_name"]
        text = item["text"]
        vector = vectors[idx]

        collection.add(
            ids=[f"table_{idx}"],
            embeddings=[vector.tolist()],
            documents=[text],
            metadatas=[{"table_name": table_name}]
        )
        print(f"✅ 已存入資料表 {table_name} 的向量")

    print("\n📦 所有資料表結構資訊已存入向量資料庫")
    return collection

# --------------------------
# 4. 主程式（不用改）
# --------------------------
if __name__ == "__student__":
    # 讀取文字
    schema_texts = get_db_schema_text()
    if not schema_texts:
        exit()

    # 提取所有文字內容
    all_texts = [item["text"] for item in schema_texts]

    # 向量化
    print("🔧 正在進行簡易向量化...")
    vectors, vectorizer = text_to_vector_simple(all_texts)
    print(f"✅ 向量化完成，向量維度：{vectors.shape[1]}")

    # 存入向量庫
    collection = save_to_chroma(schema_texts, vectors)

    # 測試查詢
    print("\n🔍 測試查詢：哪個表存學生的答題結果？")
    query_text = "哪個表存學生的答題結果？"
    query_vector = vectorizer.transform([query_text]).toarray()[0]
    results = collection.query(
        query_embeddings=[query_vector.tolist()],
        n_results=2
    )

    for i, doc in enumerate(results["documents"][0]):
        print(f"\n匹配結果 {i+1}：\n{doc}")

# 1. 在讀取完三張表的 schema_texts 後，新增表間關係文字
relation_text = """資料表名稱：table_relations
資料表註釋：學生問卷系統的表間關聯關係說明
欄位詳情：
關聯1：student表 ↔ qustionnaire_result表，關聯欄位StudentID，實現學生資訊與答題結果的關聯
關聯2：questionnaire_questions表 ↔ qustionnaire_result表，關聯欄位question_number，實現題目與答案的關聯
整體業務關係：student（學生）→ qustionnaire_result（答題）→ questionnaire_questions（題目），構成完整問卷數據鏈路
"""

# 2. 把關係文字加入列表
schema_texts.append({
    "table_name": "table_relations",
    "text": relation_text
})
