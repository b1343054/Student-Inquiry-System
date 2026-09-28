# rebuild_semantic_chroma.py
import chromadb
from sentence_transformers import SentenceTransformer
import mysql.connector

# 1. 加载预训练模型（只需要下载一次，之后永久可用）
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. 连接数据库，读取表结构
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="你的数据库密码",
    database="mobilescreenresearch"
)
cursor = conn.cursor()

# 3. 读取三张表的结构
tables = ["student", "questionnaire_questions", "qustionnaire_result"]
docs = []
metas = []

for table in tables:
    cursor.execute(f"SHOW TABLE STATUS LIKE '{table}'")
    table_comment = cursor.fetchone()[17] or ""

    cursor.execute(f"SHOW FULL COLUMNS FROM `{table}`")
    columns = cursor.fetchall()

    # 构建语义友好的文本，包含表名、注释、字段名和注释
    table_text = f"数据表：{table}，用途：{table_comment}\n字段："
    for col in columns:
        table_text += f"{col[0]}（{col[8]}）、"
    
    docs.append(table_text)
    metas.append({"table_name": table})

# 4. 生成语义向量并写入 Chroma
client = chromadb.PersistentClient(path="./chroma_db")
try:
    client.delete_collection(name="db_schema_collection")
except:
    pass
collection = client.create_collection(name="db_schema_collection")

embeddings = model.encode(docs).tolist()
collection.add(
    documents=docs,
    metadatas=metas,
    embeddings=embeddings,
    ids=[f"id_{i}" for i in range(len(docs))]
)

print("✅ 语义向量库生成完成！")
conn.close()