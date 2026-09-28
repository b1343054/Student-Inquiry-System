# 导入数据库连接库
import mysql.connector
from mysql.connector import Error

# 定义函数：读取三张表的结构并转为文本
def get_db_schema_text():
    # 指定你项目的三张目标表
    target_tables = ["student", "questionnaire_questions", "qustionnaire_result"]
    # 空列表：用来存放每张表的文本信息
    schema_texts = []

    # 1. 连接本地MySQL数据库
    try:
        conn = mysql.connector.connect(
            host="localhost",     # 本地数据库地址
            user="root",          # MySQL账号
            password="1234",      # 你的MySQL密码
            database="mobilescreenresearch"  # 你的数据库名
        )

        # 判断是否连接成功
        if conn.is_connected():
            print("✅ MySQL 数据库连接成功")
            # 创建游标，用来执行SQL语句
            cursor = conn.cursor()

            # 2. 循环遍历每一张表
            for table_name in target_tables:
                # SQL语句：查询表的字段结构
                sql = f"DESCRIBE `{table_name}`;"
                cursor.execute(sql)
                # 获取查询结果（所有字段信息）
                columns = cursor.fetchall()

                # 3. 把表结构拼接成一段自然文本（向量化需要文本格式）
                text_content = f"数据表名称：{table_name}\n"
                text_content += "字段详情：\n"

                # 遍历当前表的每一个字段
                for col in columns:
                    # col 格式：(字段名, 数据类型, 是否为空, 键类型, 默认值, 额外属性)
                    field_name = col[0]
                    field_type = col[1]
                    key_type = col[3]

                    # 判断是否是主键
                    if key_type == "PRI":
                        key_desc = "该字段为主键"
                    else:
                        key_desc = "该字段非主键"

                    # 拼接单行字段描述
                    text_content += f"字段名：{field_name}，数据类型：{field_type}，{key_desc}\n"

                # 把当前表的名称 + 文本 存入列表
                schema_texts.append({
                    "table_name": table_name,
                    "text": text_content
                })

            # 关闭游标、关闭数据库连接
            cursor.close()
            conn.close()
            return schema_texts

    # 捕获数据库连接错误
    except Error as e:
        print(f"❌ 数据库连接失败：{e}")
        return []

# 程序入口：运行函数
if __name__ == "__student__":
    result = get_db_schema_text()
    # 打印读取到的文本内容
    for item in result:
        print("----------------------------------------")
        print(item["text"])