import mysql.connector
from mysql.connector import Error
from sklearn.feature_extraction.text import CountVectorizer
import chromadb

# --------------------------
# 1. 读取数据库表结构（升级版：包含表注释和字段注释）
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
            print("✅ MySQL 数据库连接成功")
            cursor = conn.cursor()

            for table_name in target_tables:
                # --- 新增：读取表注释 ---
                cursor.execute(f"SHOW TABLE STATUS LIKE '{table_name}'")
                table_status = cursor.fetchone()
                table_comment = table_status[17] if table_status else ""

                # --- 改动：用 SHOW FULL COLUMNS 读取字段（包含注释）---
                cursor.execute(f"SHOW FULL COLUMNS FROM `{table_name}`")
                columns = cursor.fetchall()

                # 构建带注释的文本
                text_content = f"数据表名称：{table_name}\n"
                if table_comment:
                    text_content += f"表注释：{table_comment}\n"
                text_content += "字段详情：\n"

                for col in columns:
                    field_name = col[0]
                    field_type = col[1]
                    key_type = col[3]
                    field_comment = col[8]  # 第9列是字段注释

                    if key_type == "PRI":
                        key_desc = "该字段为主键"
                    else:
                        key_desc = "该字段非主键"

                    text_content += f"字段名：{field_name}，数据类型：{field_type}，{key_desc}"
                    if field_comment:
                        text_content += f"，注释：{field_comment}"
                    text_content += "\n"

                schema_texts.append({
                    "table_name": table_name,
                    "text": text_content
                })

            cursor.close()
            conn.close()
            return schema_texts

    except Error as e:
        print(f"❌ 数据库连接失败：{e}")
        return []

# --------------------------
# 2. 简易向量化（不用改）
# --------------------------
def text_to_vector_simple(texts):
    vectorizer = CountVectorizer()
    vectorizer.fit(texts)
    vectors = vectorizer.transform(texts).toarray()
    return vectors, vectorizer

# --------------------------
# 3. 存入 Chroma 向量库（不用改）
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
        print(f"✅ 已存入表 {table_name} 的向量")

    print("\n📦 所有表结构信息已存入向量数据库")
    return collection

# --------------------------
# 4. 主程序（不用改）
# --------------------------
if __name__ == "__student__":
    # 读取文本
    schema_texts = get_db_schema_text()
    if not schema_texts:
        exit()

    # 提取所有文本内容
    all_texts = [item["text"] for item in schema_texts]

    # 向量化
    print("🔧 正在进行简易向量化...")
    vectors, vectorizer = text_to_vector_simple(all_texts)
    print(f"✅ 向量化完成，向量维度：{vectors.shape[1]}")

    # 存入向量库
    collection = save_to_chroma(schema_texts, vectors)

    # 测试查询
    print("\n🔍 测试查询：哪个表存学生的答题结果？")
    query_text = "哪个表存学生的答题结果？"
    query_vector = vectorizer.transform([query_text]).toarray()[0]
    results = collection.query(
        query_embeddings=[query_vector.tolist()],
        n_results=2
    )

    for i, doc in enumerate(results["documents"][0]):
        print(f"\n匹配结果 {i+1}：\n{doc}")

# 1. 在读取完三张表的 schema_texts 后，新增表间关系文本
relation_text = """数据表名称：table_relations
表注释：学生问卷系统的表间关联关系说明
字段详情：
关联1：student表 ↔ qustionnaire_result表，关联字段StudentID，实现学生信息与答题结果的关联
关联2：questionnaire_questions表 ↔ qustionnaire_result表，关联字段question_number，实现题目与答案的关联
整体业务关系：student（学生）→ qustionnaire_result（答题）→ questionnaire_questions（题目），构成完整问卷数据链路
"""

# 2. 把关系文本加入列表
schema_texts.append({
    "table_name": "table_relations",
    "text": relation_text
})