# main_refactored.py
# 重构后的主程序，整合所有模块化组件

from flask import Flask, request, jsonify
import os
import sys

# 导入模块化组件
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.config import EMAIL_CONFIG
from src.email_handler import get_variables_from_request, process_template, convert_to_html, send_email

app = Flask(__name__)

@app.route('/send_email', methods=['POST'])
def handle_send_email():
    """
    接收 POST 请求，解析 JSON 内容后：
      1. 根据数据生成变量字典。
      2. 读取 Markdown 模板文件并替换模板中的占位符。
      3. 将替换后的内容转换为 HTML（并内联 CSS），生成纯文本版本。
      4. 发送邮件。
    """
    step_status = {}

    # 获取 JSON 数据
    data = request.get_json()
    if not data:
        step_status['获取信息'] = '错误: 请求体为空或无效 JSON'
        return jsonify({"success": False, "message": "请求体为空或不是有效的 JSON", "step_status": step_status}), 400
    step_status['获取信息'] = '成功'
    
    # 检查必须的参数 mail_recipient
    mail_recipient = data.get("mail_recipient")
    if not mail_recipient:
        step_status['检查 mail_recipient'] = '错误: 缺少 mail_recipient 参数'
        return jsonify({"success": False, "message": "缺少 mail_recipient 参数", "step_status": step_status}), 400
    step_status['检查 mail_recipient'] = '成功'
    
    # 根据请求数据生成变量字典
    variables = get_variables_from_request(data)
    step_status['生成变量'] = '成功'
    
    # 读取 Markdown 邮件模板，并进行占位符替换
    md_text, error = process_template(EMAIL_CONFIG['template_path'], variables)
    if error:
        step_status['读取邮件模板'] = f'错误: {error}'
        return jsonify({"success": False, "message": f"读取邮件模板失败: {error}", "step_status": step_status}), 500
    step_status['读取邮件模板'] = '成功'
    step_status['模板替换'] = '成功'

    # Markdown 转换为 HTML
    inlined_html, error = convert_to_html(md_text)
    if error:
        step_status['Markdown 转 HTML'] = f'错误: {error}'
        return jsonify({"success": False, "message": f"Markdown 转换失败: {error}", "step_status": step_status}), 500
    step_status['Markdown 转 HTML'] = '成功'
    step_status['内联 CSS'] = '成功'

    # 对于纯文本版，可直接使用替换后的 Markdown 文本
    plain_text = md_text

    # 发送邮件
    success, send_status = send_email(
        inlined_html,
        plain_text,
        mail_recipient,
        EMAIL_CONFIG['subject']
    )
    step_status['邮件发送'] = '成功' if success else f'错误: {send_status}'

    if success:
        return jsonify({"success": True, "message": "邮件发送成功!", "step_status": step_status})
    else:
        return jsonify({"success": False, "message": f"邮件发送失败: {send_status}", "step_status": step_status}), 500

if __name__ == '__main__':
    # 启动 Flask 服务器，监听所有网卡 5001 端口
    app.run(host='0.0.0.0', port=5001)
