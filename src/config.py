# config.py
# 配置模块，用于管理SMTP设置和其他常量配置

import os

# SMTP配置
SMTP_CONFIG = {
    'server': os.getenv('SMTP_SERVER', 'smtp.qq.com'),
    'user': os.getenv('SMTP_USER', 'space-one@qq.com'),
    'password': os.getenv('SMTP_PASSWORD', 'eudyjptmnvjffbec'),
    'port': 465
}

# 邮件模板和主题配置
_BASE_DIR = os.path.dirname(os.path.dirname(__file__))
_TEMPLATE_DIR = os.path.join(_BASE_DIR, 'templates')

EMAIL_CONFIG = {
    'shao_nian': {
        'subject': '「一场」少年探索营通知',
        'template_path': os.path.join(_TEMPLATE_DIR, '邮件内容_少年.md')
    },
    'cheng_ren': {
        'subject': '「一场」SpaceOne 视频沟通结果',
        'template_path': os.path.join(_TEMPLATE_DIR, '邮件内容_成人.md')
    }
}


# 日期格式配置
DATE_FORMAT = {
    'input': '%Y/%m/%d',
    'output': '%Y年%m月%d日',
    'month_only': '%Y年%m月'
}
