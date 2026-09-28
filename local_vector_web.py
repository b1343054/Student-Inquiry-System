import streamlit as st
import pandas as pd
from pandasql import sqldf
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
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

# 計數器
if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 0

# 讀取查詢歷史
if "query_history" not in st.session_state:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                st.session_state.query_history = json.load(f)
        except Exception:
            st.session_state.query_history = []
    else:
        st.session_state.query_history = []

# ===================== 載入並清洗 CSV 資料 =====================
@st.cache_data
def load_all_data():
    df_student = pd.read_csv(CSV_STUDENT, encoding="utf-8-sig")
    df_qustionnaire_result = pd.read_csv(CSV_RESULT, encoding="utf-8-sig")
    df_questionnaire_questions = pd.read_csv(CSV_QUESTION, encoding="utf-8-sig")

    # 清洗學院欄位：移除多餘符號
    if "College/Faculty" in df_student.columns:
        df_student["College/Faculty"] = (
            df_student["College/Faculty"]
            .astype(str)
            .str.replace(r"[()';]", "", regex=True)
            .str.strip()
        )

    # 學生表欄位重命名（兼顧原始繁簡欄位）
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

    # 問卷結果表欄位重命名
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

    return df_student, df_qustionnaire_result, df_questionnaire_questions

student, qustionnaire_result, questionnaire_questions = load_all_data()

# pandasql 執行環境
def pysqldf(sql):
    env = {
        "student": student,
        "qustionnaire_result": qustionnaire_result,
        "questionnaire_questions": questionnaire_questions
    }
    return sqldf(sql, env)

# ===================== 關鍵字與欄位對應（全繁體） =====================
TABLE_KEYWORDS = {
    "student": {
        "keywords": ["學生", "姓名", "學號", "性別", "年級", "學院", "學校", "男生", "女生"],
        "weight": 10.0
    },
    "qustionnaire_result": {
        "keywords": ["使用時長", "螢幕", "遊戲", "睡眠", "解鎖", "焦慮", "社交", "影片", "娛樂"],
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

GT_WORDS = ["超過", "大於", "以上", "多於"]
LT_WORDS = ["低於", "小於", "以下", "少於"]
AGG_KEYWORDS = {
    "COUNT": ["統計", "人數", "總數"],
    "AVG": ["平均"],
    "MAX": ["最高", "最多"],
    "MIN": ["最低", "最少"]
}

# ===================== 輕量向量比對（0 外部下載依賴） =====================
DOCS_SCHEMA = {
    "student": "學生基本資料表 包含學號 姓名 性別 年級 學校類型 學院系所 公立 私立 男 女",
    "qustionnaire_result": "學生手機使用與問卷作答結果表 包含日均螢幕總時長 社交媒體時長 遊戲時長 睡前使用時長 解鎖次數 睡眠時長 焦慮程度 自評",
    "questionnaire_questions": "問卷題目表 紀錄題目編號 題目內容 所屬問卷名稱 選項列表 答案類型"
}

@st.cache_resource
def init_vector_matcher():
    tables = list(DOCS_SCHEMA.keys())
    texts = list(DOCS_SCHEMA.values())
    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(texts)
    return tfidf, tfidf_matrix, tables

tfidf_vec, tfidf_matrix, table_keys = init_vector_matcher()

# ===================== 自然語言轉 SQL 核心函數 =====================
def generate_advanced_sql(query_text, matched_tables):
    student_table = "student"
    # 只有查詢涉及手機使用、睡眠、心理自評等指標時才需 JOIN 問卷結果表
    secondary_table = "qustionnaire_result" if any(k in query_text for k in ["時長", "时长", "螢幕", "屏幕", "遊戲", "游戏", "睡眠", "解鎖", "解锁", "焦慮", "焦虑", "自評", "自评", "社交", "影片"]) else None

    query_clean = re.sub(r"^\d+\.\s*", "", query_text)

    def clean_text(txt):
        remove = ["日均", "時長", "小時", "次數", "總", "使用", "的", "學生", "人數", "人数"]
        for w in remove:
            txt = txt.replace(w, "")
        return txt.strip()

    is_agg = False
    group_fields = []
    agg_funcs = []
    where_conds = []
    seen = set()

    # 1. 判斷統計聚合（COUNT / AVG / MAX / MIN）
    if any(k in query_clean for k in AGG_KEYWORDS["COUNT"] + AGG_KEYWORDS["AVG"] + AGG_KEYWORDS["MAX"] + AGG_KEYWORDS["MIN"]):
        is_agg = True
        target_col = None
        if secondary_table:
            for kw, col in FIELD_MAP["qustionnaire_result"].items():
                if clean_text(kw) in clean_text(query_clean):
                    target_col = f"{secondary_table}.{col}"
                    break

        if "平均" in query_clean and target_col:
            agg_funcs.append(f"AVG({target_col}) AS 平均值")
        elif ("最高" in query_clean or "最多" in query_clean) and target_col:
            agg_funcs.append(f"MAX({target_col}) AS 最大值")
        elif ("最低" in query_clean or "最少" in query_clean) and target_col:
            agg_funcs.append(f"MIN({target_col}) AS 最小值")
        else:
            agg_funcs.append("COUNT(*) AS 總人數")

        # 僅在明確提出「各」年級、「各」學院等分組維度時才 GROUP BY
        if "各年級" in query_clean or "各年级" in query_clean:
            group_fields.append(f"{student_table}.grade")
        if "各性別" in query_clean or "各性别" in query_clean:
            group_fields.append(f"{student_table}.gender")
        if "各學院" in query_clean or "各学院" in query_clean:
            group_fields.append(f"{student_table}.College_Faculty")
        if "各學校" in query_clean or "各學校類型" in query_clean:
            group_fields.append(f"{student_table}.SchoolType")

    # 2. SELECT 欄位組裝
    if is_agg:
        select_part = ", ".join(group_fields + agg_funcs)
    else:
        select_list = [
            f"{student_table}.StudentID AS 學號",
            f"{student_table}.Name AS 姓名",
            f"{student_table}.gender AS 性別",
            f"{student_table}.grade AS 年級",
            f"{student_table}.College_Faculty AS 學院"
        ]
        if secondary_table:
            for kw, col in FIELD_MAP["qustionnaire_result"].items():
                if clean_text(kw) in clean_text(query_clean):
                    select_list.append(f"{secondary_table}.{col}")
        select_part = ", ".join(select_list)

    select_clause = f"SELECT {select_part}"

    # 3. WHERE 篩選條件提取（無論是否統計查詢皆嚴格過濾）
    # 性別過濾
    if "男" in query_clean:
        c = f"{student_table}.gender IN ('男', '男生')"
        if c not in seen:
            where_conds.append(c)
            seen.add(c)
    if "女" in query_clean:
        c = f"{student_table}.gender IN ('女', '女生')"
        if c not in seen:
            where_conds.append(c)
            seen.add(c)

    # 體系過濾
    if "公立" in query_clean:
        c = f"{student_table}.SchoolType LIKE '%公立%'"
        if c not in seen:
            where_conds.append(c)
            seen.add(c)
    if "私立" in query_clean:
        c = f"{student_table}.SchoolType LIKE '%私立%'"
        if c not in seen:
            where_conds.append(c)
            seen.add(c)

    # 年級過濾（支援：一年級/大一、二年級/大二、三年級/大三、四年級/大四）
    grade_map = {
        "大一": ["一年級", "一年级", "大一", "1年級", "1年级"],
        "大二": ["二年級", "二年级", "大二", "2年級", "2年级"],
        "大三": ["三年級", "三年级", "大三", "3年級", "3年级"],
        "大四": ["四年級", "四年级", "大四", "4年級", "4年级"]
    }
    for db_grade, keywords in grade_map.items():
        if any(kw in query_clean for kw in keywords):
            c = f"{student_table}.grade = '{db_grade}'"
            if c not in seen:
                where_conds.append(c)
                seen.add(c)
            break

    # 學院過濾（智慧相容繁簡：商、醫、理、文、設）
    college_map = {
        "商": ["%商%", "%管理%"],
        "醫": ["%醫%", "%医%"],
        "理": ["%理%", "%工%"],
        "文": ["%文%", "%法%"],
        "設": ["%設%", "%设%"]
    }
    for key, patterns in college_map.items():
        if key in query_clean or (key == "醫" and "医" in query_clean) or (key == "設" and "设" in query_clean):
            sub_conds = [f"{student_table}.College_Faculty LIKE '{p}'" for p in patterns]
            c = f"({' OR '.join(sub_conds)})"
            if c not in seen:
                where_conds.append(c)
                seen.add(c)
            break

    # 數值區間過濾
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

        # 數值大於/小於過濾
        num_match = re.search(r"(超過|大於|小於|等於|大于|小于)\s*(\d+\.?\d*)", query_clean)
        if num_match:
            op_txt = num_match.group(1)
            num = num_match.group(2)
            op = ">" if op_txt in GT_WORDS or op_txt == "大于" else ("<" if op_txt in LT_WORDS or op_txt == "小于" else "=")
            for kw, col in FIELD_MAP["qustionnaire_result"].items():
                if clean_text(kw) in clean_text(query_clean):
                    c = f"{secondary_table}.{col} {op} {num}"
                    if c not in seen:
                        where_conds.append(c)
                        seen.add(c)

        # 自評分數過濾
        score_match = re.search(r"自評.*(\d+)", query_clean)
        if score_match:
            s = score_match.group(1)
            for kw, col in FIELD_MAP["qustionnaire_result"].items():
                if "自評" in kw:
                    c = f"{secondary_table}.{col} = {s}"
                    if c not in seen:
                        where_conds.append(c)
                        seen.add(c)

    # 4. 拼裝 SQL 語句
    from_clause = f"FROM {student_table}"
    if secondary_table:
        from_clause += f" JOIN {secondary_table} ON {student_table}.StudentID = {secondary_table}.StudentID"

    where_clause = f"WHERE {' AND '.join(where_conds)}" if where_conds else ""
    group_clause = f"GROUP BY {', '.join(group_fields)}" if (is_agg and group_fields) else ""

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
    user_input = st.text_input("請輸入查詢需求：", placeholder="範例：商學院總人數、查詢商學院的女生、統計各年級平均螢幕使用時長")
    submit_btn = st.form_submit_button("執行查詢")

if submit_btn:
    st.session_state.interaction_count += 1

    if not user_input.strip():
        st.warning("請輸入查詢內容！")
    else:
        with st.spinner("正在解析語意並執行查詢..."):
            # 1. 規則關鍵字計分
            table_score = {}
            for tbl, rule in TABLE_KEYWORDS.items():
                sc = sum(10 for k in rule["keywords"] if k in user_input)
                table_score[tbl] = sc

            # 2. 向量餘弦相似度加權（TF-IDF）
            try:
                user_vec = tfidf_vec.transform([user_input])
                sims = cosine_similarity(user_vec, tfidf_matrix)[0]
                for idx, sim in enumerate(sims):
                    tname = table_keys[idx]
                    table_score[tname] += round(sim * 5, 2)
            except Exception:
                pass

            # 3. 排序匹配資料表
            sorted_tbl = sorted(table_score.items(), key=lambda x: x[1], reverse=True)
            match_tables = [t for t, s in sorted_tbl]

            # 4. 生成精準 SQL
            sql_text = generate_advanced_sql(user_input, match_tables)

            # 5. 儲存紀錄
            new_rec = {
                "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "query": user_input,
                "sql": sql_text
            }
            if "query_history" not in st.session_state:
                st.session_state.query_history = []
            st.session_state.query_history.append(new_rec)
            try:
                with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                    json.dump(st.session_state.query_history, ensure_ascii=False, indent=2, fp=f)
            except Exception:
                pass

            # 6. 頁面結果輸出
            st.success("查詢語句生成完畢")
            st.subheader("資料表匹配分數")
            for t, s in sorted_tbl:
                st.write(f"{t} 匹配分數：{s:.1f}")

            st.subheader("自動生成 SQL")
            st.code(sql_text, language="sql")

            st.subheader("查詢結果")
            try:
                result_df = pysqldf(sql_text)
                st.dataframe(result_df, use_container_width=True)
            except Exception as err:
                st.error(f"執行 SQL 失敗：{str(err)}")

st.caption("按下 Enter 或點擊按鈕執行查詢")
