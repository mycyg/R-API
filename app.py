from flask import Flask, request, send_from_directory, jsonify
import os
import uuid
import docker
import shutil
from pathlib import Path
import threading
import re

app = Flask(__name__)

# 基础输出目录
BASE_OUTPUT_DIR = 'output_files'
os.makedirs(BASE_OUTPUT_DIR, exist_ok=True)

# 初始化Docker客户端
docker_client = docker.from_env()

# R执行器Docker镜像名称
R_EXECUTOR_IMAGE = 'my-r-executor:latest'

# 资源限制
CPU_LIMIT = 1  # CPU核心数
MEMORY_LIMIT = '512m'  # 内存限制
TIMEOUT = 10  # 执行超时（秒）

# 安全：禁止的模式（正则表达式）
FORBIDDEN_PATTERNS = [
    r'\bsystem\b',
    r'\bfile\b',
    r'\bunlink\b',
    r'\bsetwd\b',
    r'\bgetwd\b',
    r'\beval\b',
    r'\bparse\b',
    r'\blibrary\b',
    r'\brequire\b',
    r'\bsink\b',
    r'\binstall\.packages\b',
    r'\bread\.table\b',
    r'\bwrite\.table\b'
]

def is_code_safe(code):
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            return False
    return True

def cleanup_dir(directory):
    try:
        shutil.rmtree(directory)
    except Exception as e:
        print(f"清理目录 {directory} 时出错: {e}")

@app.route('/execute', methods=['POST'])
def execute_r_code():
    code = request.get_data(as_text=True)

    # 安全检查
    if not is_code_safe(code):
        return jsonify({'error': '代码中包含不允许的函数或模式'}), 400

    # 创建唯一的执行ID
    exec_id = uuid.uuid4().hex
    exec_dir = os.path.join(BASE_OUTPUT_DIR, exec_id)
    os.makedirs(exec_dir, exist_ok=True)

    # R脚本路径
    script_filename = 'script.R'
    script_path = os.path.join(exec_dir, script_filename)

    # 将R代码写入脚本文件
    with open(script_path, 'w') as f:
        f.write(code)

    # 准备运行Docker容器
    try:
        # 运行容器
        container = docker_client.containers.run(
            R_EXECUTOR_IMAGE,
            command=script_filename,
            volumes={
                os.path.abspath(exec_dir): {
                    'bind': '/home/ruser/code',
                    'mode': 'rw'
                }
            },
            working_dir='/home/ruser/code',
            network_disabled=True,  # 禁用网络
            detach=True,
            mem_limit=MEMORY_LIMIT,
            cpu_quota=int(CPU_LIMIT * 100000),  # Docker以100000为周期单位
            stdout=True,
            stderr=True,
            remove=True,  # 容器退出后自动删除
            cap_drop=['ALL'],  # 移除所有能力
            security_opt=["no-new-privileges"]  # 禁止新权限
        )

        # 等待容器完成执行
        exit_status = container.wait(timeout=TIMEOUT)
        logs = container.logs(stdout=True, stderr=True).decode('utf-8')

    except docker.errors.ContainerError as e:
        logs = e.stderr.decode('utf-8') if e.stderr else str(e)
        cleanup_dir(exec_dir)
        return jsonify({'error': '代码执行出错', 'details': logs}), 400
    except docker.errors.ImageNotFound:
        cleanup_dir(exec_dir)
        return jsonify({'error': f'Docker镜像 {R_EXECUTOR_IMAGE} 未找到'}), 500
    except docker.errors.APIError as e:
        cleanup_dir(exec_dir)
        return jsonify({'error': '执行代码时发生Docker API错误', 'details': str(e)}), 500
    except Exception as e:
        cleanup_dir(exec_dir)
        return jsonify({'error': '执行代码时发生未知错误', 'details': str(e)}), 500

    # 收集生成的文件（排除脚本文件）
    generated_files = [
        f for f in os.listdir(exec_dir)
        if f != script_filename
    ]

    # 生成文件的URL
    file_urls = [
        request.host_url + 'files/' + exec_id + '/' + filename
        for filename in generated_files
    ]

    # 异步清理执行目录
    threading.Thread(target=cleanup_dir, args=(exec_dir,)).start()

    return jsonify({
        'output': logs,
        'files': file_urls
    })

@app.route('/files/<exec_id>/<path:filename>', methods=['GET'])
def download_file(exec_id, filename):
    # 防止目录遍历
    if '..' in filename or filename.startswith('/'):
        return jsonify({'error': '无效的文件名'}), 400

    exec_dir = os.path.join(BASE_OUTPUT_DIR, exec_id)
    file_path = os.path.join(exec_dir, filename)
    if not os.path.isfile(file_path):
        return jsonify({'error': '文件未找到'}), 404

    return send_from_directory(exec_dir, filename, as_attachment=True)

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000)
