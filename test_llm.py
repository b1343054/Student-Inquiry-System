import requests
import json
import re

def generate_sql_by_llm(user_query, table_schema):
    url = "http://localhost:11434/api/chat"
    prompt = f"""
你是MySQL資料生成助手。
硬性規則，務必遵守：
1. 僅僅回傳純SQL程式碼，禁止輸出任何解釋、說明、備註
2. 禁止使用 ```sql 、``` 這類Markdown標籤
3. 只能使用下方提供的表與欄位，不可以自行創造欄位名稱
資料表結構：
{table_schema}
使用者查詢需求：{user_query}
"""
    payload = {
        "model": "qwen2.5:1.5b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "temperature": 0.0
    }
    res = requests.post(url, json=payload)
    data = res.json()
    raw_text = data["message"]["content"]

    # ==========自動清理標籤核心程式==========
    # 抓取出 ```sql 和 ``` 中間的SQL
    pattern = r"```sql\s*(.*?)\s*```"
    match_result = re.search(pattern, raw_text, re.DOTALL)
    if match_result:
        clean_sql = match_result.group(1)
    else:
        clean_sql = raw_text
    # 清除首尾空白換行
    clean_sql = clean_sql.strip()
    return clean_sql

# 測試內容
schema = """
student(student_id, grade_level, gender, student_name)
questionnaire_result(student_id, result_time, question_id)
questionnaire_questions(question_id, content)
關聯：
student.student_id = questionnaire_result.student_id
questionnaire_result.question_id = questionnaire_questions.question_id
"""
question = "查詢各年級平均手機使用時長"
sql_result = generate_sql_by_llm(question, schema)
print("【清理後純SQL】\n", sql_result)