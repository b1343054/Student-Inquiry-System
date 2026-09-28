import openpyxl
from db.database_handler import DatabaseHandler

class QuestionnaireImporter(DatabaseHandler):
    def __init__(self, host, user, password, database):
        super().__init__(host, user, password, database)

    def import_from_excel(self, excel_path, survey_name):
        # 打开 Excel 文件
        wb = openpyxl.load_workbook(excel_path)
        ws = wb.active

        # 跳过表头，从第2行开始读取
        for row_index, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            # 按列顺序读取：question_number, variable_name, question_text, answer_options
            question_number = row[0]
            variable_name = row[1]
            question_text = row[2]
            answer_options = row[3] if len(row) > 3 else ""

            # 跳过空行
            if not question_number:
                continue

            # 自动判断题目类型
            if answer_options and "/" in str(answer_options):
                answer_type = "single_choice"
            elif "1=" in str(answer_options) and "5=" in str(answer_options):
                answer_type = "scale_1_to_5"
            else:
                answer_type = "number_input"

            # 插入数据库
            sql = """
            INSERT INTO questionnaire_questions 
            (survey_name, question_number, variable_name, question_text, answer_type, answer_options)
            VALUES (%s, %s, %s, %s, %s, %s);
            """
            try:
                self.cursor.execute(sql, (
                    survey_name,
                    question_number,
                    variable_name,
                    question_text,
                    answer_type,
                    answer_options
                ))
                print(f"✅ 导入成功: {question_number}")
            except Exception as e:
                print(f"❌ 导入失败: {question_number}, 错误: {e}")

        # 提交所有修改
        self.connection.commit()
        print("\n📊 所有题目导入完成！")

if __name__ == "__main__":
    # 数据库配置
    host = "localhost"
    user = "root"
    password = "1234"
    database = "mobilescreenresearch"

    # 文件和问卷配置
    excel_file = "questions.xlsx"
    survey_name = "student_phone_usage_survey"

    # 运行导入
    importer = QuestionnaireImporter(host, user, password, database)
    if importer.connect():
        importer.import_from_excel(excel_file, survey_name)
    importer.close()