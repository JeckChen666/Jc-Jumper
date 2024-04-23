from flask import Flask, render_template, request, redirect, url_for
import os
import random
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta, timezone
import threading

app = Flask(__name__, static_folder='templates/static')

# 设置时区为东八区
eastern_eight_timezone = timezone(timedelta(hours=8))
# 配置日志记录
log_dir = './logs'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# 检查日志目录是否存在，如果不存在则创建
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
handler = TimedRotatingFileHandler(
    filename=os.path.join(log_dir, 'app.log'),
    when='midnight',
    interval=1,
    backupCount=15,
    encoding='utf-8'
)
formatter = logging.Formatter('%(asctime)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# 初始化字典，用于跟踪每个 IP 地址的错误次数和最后一次请求时间
ip_error_count = {}
ip_last_request_time = {}

# 初始化全局变量，用于保存上次读取的特定网址
specific_url = ""


# 生成随机的加减法算式
def generate_question():
    num1 = random.randint(1, 100)
    num2 = random.randint(1, num1)  # 第二个数不超过第一个数
    operator = random.choice(['+', '-'])
    if operator == '-' and num1 < num2:  # 如果运算符是减法且结果为负数，则交换数值和运算符
        num1, num2 = num2, num1
    question = f"{num1} {operator} {num2}"
    answer = eval(question)
    return question, answer


# 每小时读取一次配置文件，更新特定网址
def update_specific_url():
    global specific_url

    with open('config.txt', 'r') as f:
        specific_url = f.readline().strip()

    logger.info(f"特定网址已更新为：{specific_url}")

    # 每隔一个小时再次执行更新
    threading.Timer(3600, update_specific_url).start()


# 初始化特定网址
update_specific_url()


# 首页路由
@app.route('/', methods=['GET', 'POST'])
def home():
    global ip_error_count
    global ip_last_request_time

    if request.method == 'POST':
        user_answer = request.form.get('answer')
        correct_answer = request.form.get('correct_answer')
        question = request.form.get('question')
        ip_address = request.remote_addr

        # 检查 IP 的错误次数
        if ip_address not in ip_error_count:
            ip_error_count[ip_address] = 0
        else:
            last_request_time = ip_last_request_time.get(ip_address, datetime.min)
            if datetime.now() - last_request_time > timedelta(hours=1):
                ip_error_count[ip_address] = 0

        # 更新 IP 的错误次数和最后一次请求时间
        if user_answer != correct_answer:
            ip_error_count[ip_address] += 1
        else:
            ip_error_count[ip_address] = 0
        ip_last_request_time[ip_address] = datetime.now()

        # 记录 IP 被限制访问的信息
        if ip_error_count[ip_address] >= 10:
            log_entry = f"IP地址 {ip_address} 已被限制访问，错误次数达到 {ip_error_count[ip_address]}，请稍后再试。"
            logger.info(log_entry)
            return "您的 IP 地址已被限制访问，请稍后再试。"

        ip_address = request.remote_addr
        request_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result = "正确" if user_answer == correct_answer else "错误"
        error_count = ip_error_count[ip_address]

        log_entry = f"IP地址: {ip_address}, 请求时间: {request_time}, 题目内容: {question}, 用户输入: {user_answer}, 判断结果: {result}, 错误次数: {error_count}"
        logger.info(log_entry)

        if user_answer == correct_answer:
            return redirect(specific_url)  # 从配置文件中读取的特定网址
        else:
            question, answer = generate_question()
            return render_template('index.html', question=question, correct_answer=answer,
                                   message="答案错误，请重新作答")

    question, answer = generate_question()
    return render_template('index.html', question=question, correct_answer=answer, message="")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
