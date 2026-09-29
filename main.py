from db.questionnaire_dao import QuestionnaireDAO

if __name__ == "__student__":
    # 資料庫連線配置
    host = "localhost"
    user = "root"
    password = "1234"
    db_name = "mobilescreenresearch"

    # 建立問卷操作物件
    q_dao = QuestionnaireDAO(host, user, password, db_name)

    # 連線資料庫
    if q_dao.connect():
        # 指定要查詢的問卷名稱
        target_survey = "student_phone_usage_survey"
        # 呼叫查詢方法
        questions = q_dao.get_questions_by_survey(target_survey)

        print(f"\n📋 問卷 [{target_survey}] 的所有題目：")
        print("-" * 50)
        for q in questions:
            print(f"題號: {q[0]}")
            print(f"變數名稱: {q[1]}")
            print(f"題目: {q[2]}")
            print(f"類型: {q[3]}")
            print(f"選項: {q[4]}\n")

    # 關閉連線
    q_dao.close()
