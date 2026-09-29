# rebuild_semantic_chroma.py
import chromadb
from sentence_transformers import SentenceTransformer
import mysql.connector

# 1. 載入預訓練模型（只需要下載一次，之後永久可用）
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. 連線資料庫，讀取資料表結構
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="你的資料庫密碼",
    database="mobilescreenresearch"
)
cursor = conn.cursor()

# 3. 讀取三張表的結構
tables = ["student", "questionnaire_questions", "qustionnaire_result"]
docs = []
metas = []

for table in tables:
    cursor.execute(f"SHOW TABLE STATUS LIKE '{table}'")
    table_comment = cursor.fetchone()[17] or ""

    cursor.execute(f"SHOW FULL COLUMNS FROM `{table}`")
    columns = cursor.fetchall()

    # 建構語意友好的文字，包含資料表名稱、註釋、欄位名稱與註釋
    table_text = f"資料表：{table}，用途：{table_comment}\n欄位："
    for col in columns:
        table_text += f"{col[0]}（{col[8]}）、"
    
    docs.append(table_text)
    metas.append({"table_name": table})

# 4. 生成語意向量並寫入 Chroma
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

print("✅ 語意向量庫生成完成！")
conn.close()
