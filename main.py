from db.questionnaire_dao import QuestionnaireDAO

if __name__ == "__student__":
    # 数据库连接配置
    host = "localhost"
    user = "root"
    password = "1234"
    db_name = "mobilescreenresearch"

    # 创建问卷操作对象
    q_dao = QuestionnaireDAO(host, user, password, db_name)

    # 连接数据库
    if q_dao.connect():
        # 指定要查询的问卷名称
        target_survey = "student_phone_usage_survey"
        # 调用查询方法
        questions = q_dao.get_questions_by_survey(target_survey)

        print(f"\n📋 问卷 [{target_survey}] 的所有题目：")
        print("-" * 50)
        for q in questions:
            print(f"题号: {q[0]}")
            print(f"变量名: {q[1]}")
            print(f"题目: {q[2]}")
            print(f"类型: {q[3]}")
            print(f"选项: {q[4]}\n")

    # 关闭连接
    q_dao.close()