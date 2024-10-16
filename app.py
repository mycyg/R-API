import os
import subprocess
import uuid
import requests
from flask import Flask, request, jsonify, url_for

app = Flask(__name__)

# 设置静态文件存储目录
app.config['UPLOAD_FOLDER'] = 'static'

@app.route('/run-r', methods=['POST'])
def run_r():
    # 生成唯一的ID
    unique_id = str(uuid.uuid4())
    r_file = f'input_{unique_id}.R'
    result_file = f'result_{unique_id}.txt'
    output_image = f'output_{unique_id}.png'  # 假设输出图像为PNG格式
    csv_file = None

    # 创建静态文件目录，如果不存在则创建
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # 处理输入的文件URL
    file_url = request.form.get('file_url')
    if file_url:
        # 从URL下载文件
        csv_file = os.path.join(app.config['UPLOAD_FOLDER'], f'input_{unique_id}.csv')
        response = requests.get(file_url)
        
        # 检查是否成功下载文件
        if response.status_code == 200:
            with open(csv_file, 'wb') as f:
                f.write(response.content)
        else:
            return jsonify({'error': 'Failed to download file from URL'}), 400

    # 获取 R 代码
    r_code = request.form.get('code')
    if r_code:
        with open(r_file, 'w') as f:
            f.write(r_code)

    try:
        # 构建 Docker 镜像（如果未构建）
        subprocess.run(['docker', 'build', '-t', 'r-script-runner', '.'])

        # 运行 Docker 容器，执行 R 代码并生成图像或文件
        result = subprocess.run(
            ['docker', 'run', '--rm', '-v', f'{os.getcwd()}:/usr/src/app', 'r-script-runner', r_file, result_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # 检查生成的输出图像文件
        output_image_path = os.path.join(app.config['UPLOAD_FOLDER'], output_image)
        if os.path.exists(output_image_path):
            download_link = url_for('static', filename=output_image, _external=True)
            return jsonify({'download_link': download_link})

        # 如果没有生成图像文件，返回文本结果
        with open(result_file, 'r') as f:
            output = f.read()

        return jsonify({'output': output})

    finally:
        # 清理R代码和结果文件
        if os.path.exists(r_file):
            os.remove(r_file)
        if os.path.exists(result_file):
            os.remove(result_file)
        if csv_file and os.path.exists(csv_file):
            os.remove(csv_file)

if __name__ == '__main__':
    app.run(debug=True)
