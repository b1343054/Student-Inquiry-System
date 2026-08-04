import streamlit as st
import chromadb
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from pandasql import sqldf
import re
import json
import os
import datetime

# ===================== 檔案路徑 =====================
CSV_STUDENT = "student_202608041611.csv"
CSV_RESULT = "qustionnaire_result_202608041611.csv"
CSV_QUESTION = "questionnaire_questions_202608041611.csv"
HISTORY_FILE = "query_history.json"

# 頁面設定
st.set_page_config(page_title="學生手機使用查詢系統", layout="wide")
st.title("🔍 學生手機螢幕使用資料查詢工具")

# 清空舊快取
st.cache_data.clear()
st.cache_resource.clear()

# 計數器
if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 0

# 讀取查詢歷史
if "query_history" not in st.session_state:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            st.session_state.query_history = json.load(f)
    else:
        st.session_state.query_history = []

# ===================== 載入並清洗CSV資料 =====================
def load_all_data():
    df_student = pd.read_csv(CSV_STUDENT, encoding="utf-8-sig")
    df_qustionnaire_result = pd.read_csv(CSV_RESULT, encoding="utf-8-sig")
    df_questionnaire_questions = pd.read_csv(CSV_QUESTION, encoding="utf-8-sig")

    # 清洗學院欄：移除 () ' ; 等髒符號
    if "College/Faculty" in df_student.columns:
        df_student["College/Faculty"] = (
            df_student["College/Faculty"]
            .astype(str)
            .str.replace(r"[()';]", "", regex=True)
            .str.strip()
        )

    # 學生表欄位重命名
    student_col_map = {
        "學號": "StudentID",
        "学号": "StudentID",
        "姓名": "Name",
        "性別": "gender",
        "性别": "gender",
        "年級": "grade",
        "年级": "grade",
        "學校類型": "SchoolType",
        "学校类型": "SchoolType",
        "College/Faculty": "College_Faculty"
    }
    df_student = df_student.rename(columns=student_col_map)

    # 問卷作答表欄位重命名
    result_col_map = {
        "學生學號": "StudentID",
        "學生編號": "StudentID",
        "学生编号": "StudentID",
        "日均手機螢幕使用總時長": "DailyAvgScreenTime",
        "日均手机屏幕使用总时长": "DailyAvgScreenTime",
        "日均社交媒體使用時長": "DailyAvgSocialMediaTime",
        "日均社交媒体使用时长": "DailyAvgSocialMediaTime",
        "日均視頻/娛樂APP使用時長": "DailyAvgVideoTime",
        "日均视频/娱乐APP使用时长": "DailyAvgVideoTime",
        "日均手機遊戲使用時長": "DailyAvgGameTime",
        "日均手机游戏使用时长": "DailyAvgGameTime",
        "睡前手機使用時長": "DailyAvgBedtimePhoneTime",
        "睡前手机使用时长": "DailyAvgBedtimePhoneTime",
        "日均手機解鎖次數": "DailyAvgUnlockCount",
        "日均手机解锁次数": "DailyAvgUnlockCount",
        "日均睡眠時長": "DailyAvgSleepDuration",
        "日均睡眠时长": "DailyAvgSleepDuration",
        "手機使用對學業的影響自評": "ImpactOnAcademic",
        "手机使用对学业的影响自评": "ImpactOnAcademic",
        "手機使用對睡眠質量的影響自評": "ImpactOnSleep",
        "手机使用对睡眠质量自评": "ImpactOnSleep",
        "無手機時的焦慮程度": "AnxietyWithoutPhone",
        "无手机焦虑程度": "AnxietyWithoutPhone"
    }
    df_qustionnaire_result = df_qustionnaire_result.rename(columns=result_col_map)

    # 題目表欄位重命名
    question_col_map = {
        "題目編號": "id",
        "题目编号": "id",
        "題目內容": "question_text",
        "题目内容": "question_text",
        "所屬問卷名稱": "survey_name",
        "所属问卷名称": "survey_name",
        "答案類型": "answer_type",
        "答案类型": "answer_type",
        "題目選項列表": "answer_options",
        "题目选项列表": "answer_options"
    }
    df_questionnaire_questions = df_questionnaire_questions.rename(columns=question_col_map)

    # 除錯輸出
    print("===== student 清洗後欄位 =====")
    print(df_student.columns.tolist())
    print("===== result 清洗後欄位 =====")
    print(df_qustionnaire_result.columns.tolist())

    return df_student, df_qustionnaire_result, df_questionnaire_questions

# 載入全域資料
student, qustionnaire_result, questionnaire_questions = load_all_data()

# pandasql 執行函數
def pysqldf(sql):
    env = {
        "student": student,
        "qustionnaire_result": qustionnaire_result,
        "questionnaire_questions": questionnaire_questions
    }
    return sqldf(sql, env)

# ===================== 關鍵字配置 =====================
TABLE_KEYWORDS = {
    "student": {
        "keywords": ["學生", "学生", "姓名", "學號", "性別", "年級", "學院", "學校"],
        "weight": 10.0
    },
    "qustionnaire_result": {
        "keywords": ["使用時長", "螢幕", "遊戲", "睡眠", "解鎖", "焦慮"],
        "weight": 10.0
    },
    "questionnaire_questions": {
        "keywords": ["問卷", "題目", "選項"],
        "weight": 10.0
    }
}

FIELD_MAP = {
    "student": {
        "學號": "StudentID",
        "姓名": "Name",
        "性別": "gender",
        "年級": "grade",
        "學校類型": "SchoolType",
        "學院": "College_Faculty"
    },
    "qustionnaire_result": {
        "學生學號": "StudentID",
        "日均螢幕總時長": "DailyAvgScreenTime",
        "社交媒體時長": "DailyAvgSocialMediaTime",
        "影片娛樂時長": "DailyAvgVideoTime",
        "遊戲時長": "DailyAvgGameTime",
        "睡前手機時長": "DailyAvgBedtimePhoneTime",
        "解鎖次數": "DailyAvgUnlockCount",
        "睡眠時長": "DailyAvgSleepDuration",
        "學業影響": "ImpactOnAcademic",
        "睡眠影響": "ImpactOnSleep",
        "無手機焦慮": "AnxietyWithoutPhone"
    },
    "questionnaire_questions": {
        "題號": "id",
        "題目": "question_text",
        "問卷名稱": "survey_name"
    }
}

GT_WORDS = ["超過", "超过", "大於", "大于", "以上", "多於", "多于"]
LT_WORDS = ["低於", "低于", "小於", "小于", "以下", "少於", "少于"]
AGG_KEYWORDS = {
    "COUNT": ["統計", "人數"],
    "AVG": ["平均"],
    "MAX": ["最高"],
    "MIN": ["最低"]
}

# ===================== 向量庫初始化 =====================
@st.cache_resource
def init_vector():
    client = chromadb.PersistentClient(path="./chroma_db")
    coll = client.get_collection("db_schema_collection")
    docs = coll.get()["documents"]
    vec = TfidfVectorizer()
    vec.fit(docs)
    return coll, vec

collection, vectorizer = init_vector()

# ===================== 自然語言轉SQL核心函數 =====================
def generate_advanced_sql(query_text, matched_tables):
    student_table = "student" if "student" in matched_tables else None
    secondary_table = "qustionnaire_result" if "qustionnaire_result" in matched_tables else None
    query_clean = re.sub(r"^\d+\.\s*", "", query_text)

    def clean_text(txt):
        remove = ["日均", "時長", "小时", "次數", "總", "使用", "的", "學生"]
        for w in remove:
            txt = txt.replace(w, "")
        return txt.strip()

    is_agg = False
    group_fields = []
    agg_funcs = []

    # 判斷是否統計查詢
    if any(k in query_clean for k in AGG_KEYWORDS["COUNT"] + AGG_KEYWORDS["AVG"] + AGG_KEYWORDS["MAX"] + AGG_KEYWORDS["MIN"]):
        is_agg = True
        target_col = None
        for kw, col in FIELD_MAP["qustionnaire_result"].items():
            if clean_text(kw) in clean_text(query_clean):
                target_col = f"{secondary_table}.{col}"
                break

        if "平均" in query_clean and target_col:
            agg_funcs.append(f"AVG({target_col}) AS 平均值")
        elif "最高" in query_clean and target_col:
            agg_funcs.append(f"MAX({target_col}) AS 最大值")
        elif "最低" in query_clean and target_col:
            agg_funcs.append(f"MIN({target_col}) AS 最小值")
        else:
            agg_funcs.append("COUNT(*) AS 總人數")

        # 分組欄位
        if "性別" in query_clean:
            group_fields.append(f"{student_table}.gender")
        if "年級" in query_clean:
            group_fields.append(f"{student_table}.grade")
        if "學院" in query_clean:
            group_fields.append(f"{student_table}.College_Faculty")
        if "公立" in query_clean or "私立" in query_clean:
            group_fields.append(f"{student_table}.SchoolType")

    # 選取欄位
    if is_agg:
        select_part = ", ".join(group_fields + agg_funcs)
    else:
        select_list = [
            f"{student_table}.StudentID AS 學號",
            f"{student_table}.Name AS 姓名",
            f"{student_table}.College_Faculty AS 學院"
        ]
        if secondary_table:
            for kw, col in FIELD_MAP["qustionnaire_result"].items():
                if clean_text(kw) in clean_text(query_clean):
                    select_list.append(f"{secondary_table}.{col}")
        select_part = ", ".join(select_list)

    select_clause = f"SELECT {select_part}"

    # WHERE條件收集
    where_conds = []
    seen = set()

    if not is_agg:
        # 性別篩選
        if "男" in query_clean:
            c = f"{student_table}.gender = '男'"
            if c not in seen:
                where_conds.append(c)
                seen.add(c)
        if "女" in query_clean:
            c = f"{student_table}.gender = '女'"
            if c not in seen:
                where_conds.append(c)
                seen.add(c)

        # 公立私立
        if "公立" in query_clean:
            c = f"{student_table}.SchoolType = '公立'"
            if c not in seen:
                where_conds.append(c)
                seen.add(c)
        if "私立" in query_clean:
            c = f"{student_table}.SchoolType = '私立'"
            if c not in seen:
                where_conds.append(c)
                seen.add(c)

        # 學院篩選
        if "商管學院" in query_clean:
            c = f"{student_table}.College_Faculty = '商管学院'"
            if c not in seen:
                where_conds.append(c)
                seen.add(c)

    # 數值區間判斷
    if secondary_table:
        range_match = re.search(r"(\d+\.?\d*)\s*[~至-]\s*(\d+)", query_clean)
        if range_match:
            min_num = range_match.group(1)
            max_num = range_match.group(2)
            qc = clean_text(query_clean)
            for kw, col in FIELD_MAP["qustionnaire_result"].items():
                if clean_text(kw) in qc:
                    c1 = f"{secondary_table}.{col} >= {min_num}"
                    c2 = f"{secondary_table}.{col} <= {max_num}"
                    if c1 not in seen:
                        where_conds.append(c1)
                        seen.add(c1)
                    if c2 not in seen:
                        where_conds.append(c2)
                        seen.add(c2)

        # 大於/小於判斷
        num_match = re.search(r"(超過|大於|小於|等於)\s*(\d+\.?\d*)", query_clean)
        if num_match:
            op_txt = num_match.group(1)
            num = num_match.group(2)
            op = "="
            if op_txt in GT_WORDS:
                op = ">"
            if op_txt in LT_WORDS:
                op = "<"
            for kw, col in FIELD_MAP["qustionnaire_result"].items():
                if clean_text(kw) in clean_text(query_clean):
                    c = f"{secondary_table}.{col} {op} {num}"
                    if c not in seen:
                        where_conds.append(c)
                        seen.add(c)

        # 自評分數篩選
        score_match = re.search(r"自評.*(\d+)", query_clean)
        if score_match:
            s = score_match.group(1)
            for kw, col in FIELD_MAP["qustionnaire_result"].items():
                if "自評" in kw:
                    c = f"{secondary_table}.{col} = {s}"
                    if c not in seen:
                        where_conds.append(c)
                        seen.add(c)

    # FROM & JOIN
    from_clause = f"FROM {student_table}"
    if secondary_table:
        from_clause += f" JOIN {secondary_table} ON {student_table}.StudentID = {secondary_table}.StudentID"

    # WHERE拼接
    where_clause = f"WHERE {' AND '.join(where_conds)}" if where_conds else ""

    # GROUP BY
    group_clause = f"GROUP BY {', '.join(group_fields)}" if (is_agg and group_fields) else ""

    # 組合完整SQL
    full_sql = f"{select_clause} {from_clause}"
    if where_clause:
        full_sql += f" {where_clause}"
    if group_clause:
        full_sql += f" {group_clause}"

    return full_sql

# ===================== 側邊欄介面 =====================
with st.sidebar.expander("📊 查詢統計"):
    st.metric("累計查詢次數", st.session_state.interaction_count)
    st.divider()

with st.sidebar.expander("📜 查詢紀錄"):
    if st.button("清除全部紀錄"):
        st.session_state.query_history = []
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        st.rerun()

    if not st.session_state.query_history:
        st.info("尚無查詢紀錄")
    else:
        for rec in reversed(st.session_state.query_history[-10:]):
            with st.expander(rec["time"]):
                st.text("查詢：" + rec["query"])
                st.code(rec["sql"], language="sql")

# ===================== 主查詢介面 =====================
with st.form("query_form"):
    user_input = st.text_input("請輸入查詢需求：", placeholder="範例：查詢商管學院女生、統計各年級平均手機使用時長")
    submit_btn = st.form_submit_button("執行查詢")

if submit_btn:
    st.session_state.interaction_count += 1

    if not user_input.strip():
        st.warning("請輸入查詢內容！")
    else:
        with st.spinner("正在解析並查詢資料..."):
            # 表匹配計算
            table_score = {}
            for tbl, rule in TABLE_KEYWORDS.items():
                sc = sum(10 for k in rule["keywords"] if k in user_input)
                table_score[tbl] = sc

            # 向量匹配，過濾不存在的table_name
            vec_in = vectorizer.transform([user_input]).toarray()
            res = collection.query(query_embeddings=vec_in, n_results=8)

            for idx, dist in enumerate(res["distances"][0]):
                tname = res["metadatas"][0][idx]["table_name"]
                if tname in table_score:
                    table_score[tname] += round(5 - dist, 2)

            # 排序匹配表
            sorted_tbl = sorted(table_score.items(), key=lambda x: x[1], reverse=True)
            match_tables = [t for t, s in sorted_tbl]

            # 產生SQL
            sql_text = generate_advanced_sql(user_input, match_tables)

            # 儲存紀錄
            new_rec = {
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "query": user_input,
                "sql": sql_text
            }
            if "query_history" not in st.session_state:
                st.session_state.query_history = []
            st.session_state.query_history.append(new_rec)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(st.session_state.query_history, ensure_ascii=False, indent=2, fp=f)

            # 頁面輸出
            st.success("查詢語句生成完畢")
            st.subheader("資料表匹配分數")
            for t, s in sorted_tbl:
                st.write(f"{t} 匹配分數：{s:.1f}")

            st.subheader("自動生成SQL")
            st.code(sql_text, language="sql")

            st.subheader("查詢結果")
            try:
                result_df = pysqldf(sql_text)
                st.dataframe(result_df, use_container_width=True)
            except Exception as err:
                st.error(f"執行SQL失敗：{str(err)}")

st.caption("按下Enter或點擊按鈕執行查詢")