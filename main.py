# main_refactored.py
# 重构后的主程序，整合所有模块化组件

from flask import Flask, request, jsonify
import traceback
import os
import sys

# 导入模块化组件
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.config import EMAIL_CONFIG
from src.email_handler import get_variables_from_request, process_template, convert_to_html, send_email

app = Flask(__name__)

def make_response(success, message, step_status, http_code=200):
    """统一的 JSON 响应封装。"""
    return jsonify({"success": success, "message": message, "step_status": step_status}), http_code

@app.route('/send_email', methods=['POST'])
def handle_send_email():
    """处理发送邮件请求：校验参数、渲染模板、发送邮件。"""
    step_status = {}
    try:
        # 获取 JSON 数据
        data = request.get_json()
        if not data:
            step_status['获取信息'] = '错误: 请求体为空或无效 JSON'
            return make_response(False, '请求体为空或不是有效的 JSON', step_status, 400)
        step_status['获取信息'] = '成功'

        # 检查必须的参数 spaceone_mail_recipient（收件人邮箱）
        recipient = data.get('spaceone_mail_recipient')
        if not recipient:
            step_status['检查 spaceone_mail_recipient'] = '错误: 缺少 spaceone_mail_recipient 参数'
            return make_response(False, '缺少 spaceone_mail_recipient 参数', step_status, 400)
        step_status['检查 spaceone_mail_recipient'] = '成功'

        # 检查必须的业务参数 spaceone_child_name（其余变量由服务端生成）
        if not data.get("spaceone_child_name"):
            step_status['检查 spaceone_child_name'] = '错误: 缺少 spaceone_child_name 参数'
            return make_response(False, '缺少 spaceone_child_name 参数', step_status, 400)
        step_status['检查 spaceone_child_name'] = '成功'
        
        # 根据请求数据生成变量字典
        variables = get_variables_from_request(data)
        step_status['生成变量'] = '成功'
        
        # 读取 Markdown 邮件模板，并进行占位符替换
        md_text, error = process_template(EMAIL_CONFIG['template_path'], variables)
        if error:
            step_status['读取邮件模板'] = f'错误: {error}'
            return make_response(False, f'读取邮件模板失败: {error}', step_status, 500)
        step_status['读取邮件模板'] = '成功'
        step_status['模板替换'] = '成功'

        # Markdown 转换为 HTML
        inlined_html, error = convert_to_html(md_text)
        if error:
            step_status['Markdown 转 HTML'] = f'错误: {error}'
            return make_response(False, f'Markdown 转换失败: {error}', step_status, 500)
        step_status['Markdown 转 HTML'] = '成功'
        step_status['内联 CSS'] = '成功'

        # 对于纯文本版，可直接使用替换后的 Markdown 文本
        plain_text = md_text

        # 发送邮件（若 send_email 抛出异常也会被兜底捕获）
        success, send_status = send_email(
            inlined_html,
            plain_text,
            recipient,
            EMAIL_CONFIG['subject']
        )
        step_status['邮件发送'] = '成功' if success else f'错误: {send_status}'

        if success:
            return make_response(True, '邮件发送成功!', step_status)
        else:
            return make_response(False, f'邮件发送失败: {send_status}', step_status, 500)
    except Exception as e:
        # 兜底捕获，打印堆栈并返回 JSON，且不发送邮件
        step_status['未捕获异常'] = str(e)
        print('Unhandled error in /send_email:', e)
        print(traceback.format_exc())
        return make_response(False, f'内部错误: {e}', step_status, 500)

if __name__ == '__main__':
    # 启动 Flask 服务器，监听所有网卡，端口可通过环境变量 PORT 配置
    port = int(os.getenv('PORT', '5001'))
    app.run(host='0.0.0.0', port=port)
