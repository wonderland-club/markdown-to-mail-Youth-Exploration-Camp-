# email_handler.py
# 邮件处理模块，负责邮件模板处理、变量替换、HTML转换和发送

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pypandoc
from premailer import transform
from datetime import datetime, timedelta
import pytz
import re
from config import SMTP_CONFIG, EMAIL_CONFIG, DATE_FORMAT

def get_variables_from_request(data):
    """
    根据 POST 请求的 JSON 数据生成邮件模板替换用的变量字典。
    如果请求中未提供某变量，则使用预设默认值。
    """
    variables = {}
    # 使用请求数据中的变量，或使用默认值
    variables['spaceone_name'] = data.get('spaceone_name')
    variables['spaceone_phase'] = data.get('spaceone_phase')
    variables['spaceone_paragraph'] = data.get('spaceone_paragraph')
    variables['spaceone_offerings'] = data.get('spaceone_offerings')
    variables['spaceone_cost'] = data.get('spaceone_cost')
    variables['spaceone_current_time'] = datetime.now().strftime(DATE_FORMAT['output'])
    variables['spaceone_fees_Deadline'] = (datetime.now(pytz.timezone('Asia/Shanghai')) + timedelta(days=3)).strftime(DATE_FORMAT['output'])
    variables['spaceone_member_start'] = data.get('spaceone_member_start')
    
    try:
        # 解析原始日期格式：例如 "2025/05/01"
        dt_member_start = datetime.strptime(variables['spaceone_member_start'], DATE_FORMAT['input'])
        # 将格式转换为 "YYYY年MM月DD日"
        variables['spaceone_member_start'] = dt_member_start.strftime(DATE_FORMAT['output'])
        # 计算 +1 天后的日期，并格式化
        dt_member_start_1 = dt_member_start + timedelta(days=1)
        variables['spaceone_member_start_1'] = dt_member_start_1.strftime(DATE_FORMAT['output'])
    except Exception as e:
        variables['spaceone_member_start'] = '0000年0月0日'
        variables['spaceone_member_start_1'] = '0000年0月0日'
    
    # 修改此处：将 spaceone_membership_end 转换为年月日格式，不需要默认值
    membership_end = data.get('spaceone_membership_end')
    if membership_end:
        dt_membership_end = datetime.strptime(membership_end, DATE_FORMAT['input'])
        variables['spaceone_membership_end'] = dt_membership_end.strftime(DATE_FORMAT['output'])
    else:
        variables['spaceone_membership_end'] = None

    return variables

def process_template(template_path, variables):
    """
    读取Markdown模板并替换变量
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            md_text = f.read()
        
        # 替换模板中所有以 {{&key}} 格式的占位符
        for key, value in variables.items():
            md_text = md_text.replace('{{&' + key + '}}', str(value))
        
        return md_text, None
    except Exception as e:
        return None, str(e)

def convert_to_html(md_text):
    """
    将Markdown文本转换为HTML并内联CSS
    """
    try:
        html_content = pypandoc.convert_text(md_text, 'html', format='md')
        
        # 内联 CSS 样式
        basic_css = """
        body {     font-family: Arial, sans-serif;     font-size: 14px;     line-height: 1.6;     color: black !important; } 
        h1, h2, h3 {     color: black; } 
        p {     margin: 10px 0; } 
        ul, ol {     margin: 10px 0;     padding-left: 20px; } 
        code {     padding: 2px 4px;     border-radius: 3px; } 
        a:link, a:visited {     color: black;     text-decoration: none; } 
        a:hover {     color: black; } 
        .im {     color: black !important;     font-family: Arial, sans-serif;     font-size: 14px;     line-height: 1.6; }
        """
        html_with_css = f"<style>{basic_css}</style>{html_content}"
        inlined_html = transform(html_with_css)
        
        return inlined_html, None
    except Exception as e:
        return None, str(e)

def send_email(html_content, plain_text, mail_recipient, subject):
    """
    根据生成的邮件内容，利用 SMTP 发送邮件。

    参数:
        html_content (str): 内嵌 CSS 样式的 HTML 邮件内容
        plain_text (str): 纯文本格式邮件内容
        mail_recipient (str): 收件人邮箱
        subject (str): 邮件主题
    """
    # 从配置获取SMTP设置
    SMTP_SERVER = SMTP_CONFIG['server']
    SMTP_USER = SMTP_CONFIG['user']
    SMTP_PASSWORD = SMTP_CONFIG['password']
    SMTP_PORT = SMTP_CONFIG['port']
    
    # 构造多部分邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = SMTP_USER
    msg['To'] = mail_recipient

    # 添加纯文本和 HTML 内容
    msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    # 不再附加任何附件
    
    try:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, mail_recipient, msg.as_string())
        server.quit()
        print("邮件发送成功!")
        return True, "邮件发送成功"
    except Exception as e:
        print("邮件发送错误:", str(e))
        return False, str(e)
