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
from config import SMTP_CONFIG, DATE_FORMAT

SHAO_NIAN = 'shao_nian'
CHENG_REN = 'cheng_ren'


def _base_time_context():
    tz_sh = pytz.timezone('Asia/Shanghai')
    now_sh = datetime.now(tz_sh)
    return now_sh, (now_sh + timedelta(days=3))


def get_variables_from_request(data, template_type):
    """根据不同模板类型生成变量字典。"""
    now_sh, deadline_sh = _base_time_context()
    current_date = now_sh.strftime(DATE_FORMAT['output'])
    deadline_date = deadline_sh.strftime(DATE_FORMAT['output'])

    if template_type == SHAO_NIAN:
        child_name = data.get('spaceone_child_name')
        if not child_name:
            return None, '缺少 spaceone_child_name 参数'

        variables = {
            'spaceone_child_name': child_name,
            'spaceone_current_time': current_date,
            'spaceone_Payment_deadline': deadline_date
        }
        return variables, None

    if template_type == CHENG_REN:
        required_fields = [
            'spaceone_name',
            'spaceone_phase',
            'spaceone_product',
            'spaceone_cost'
        ]

        missing_keys = [field for field in required_fields if not data.get(field)]
        if missing_keys:
            return None, f"缺少必要参数: {', '.join(missing_keys)}"

        variables = {
            'spaceone_name': data.get('spaceone_name'),
            'spaceone_phase': data.get('spaceone_phase'),
            'spaceone_product': data.get('spaceone_product'),
            'spaceone_cost': data.get('spaceone_cost'),
            'spaceone_fees_Deadline': deadline_date,
            'spaceone_current_time': current_date
        }
        return variables, None

    return None, f'未知的模板类型: {template_type}'

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

def send_email(html_content, plain_text, mail_recipient, subject, cc_recipients=None):
    """
    根据生成的邮件内容，利用 SMTP 发送邮件。

    参数:
        html_content (str): 内嵌 CSS 样式的 HTML 邮件内容
        plain_text (str): 纯文本格式邮件内容
        mail_recipient (str): 收件人邮箱
        subject (str): 邮件主题
        cc_recipients (List[str], optional): 抄送邮箱列表
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
    if cc_recipients:
        msg['Cc'] = ', '.join(cc_recipients)

    # 添加纯文本和 HTML 内容
    msg.attach(MIMEText(plain_text, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    # 不再附加任何附件
    
    try:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context)
        server.login(SMTP_USER, SMTP_PASSWORD)
        recipients = [mail_recipient]
        if cc_recipients:
            recipients.extend(cc_recipients)
        server.sendmail(SMTP_USER, recipients, msg.as_string())
        server.quit()
        print("邮件发送成功!")
        return True, "邮件发送成功"
    except Exception as e:
        print("邮件发送错误:", str(e))
        return False, str(e)
