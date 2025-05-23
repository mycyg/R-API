from flask import Flask, request, send_from_directory, jsonify
import os
import uuid
import docker
import shutil
from pathlib import Path
import threading
import re
import time
import config # Added import for config.py
import logging # Added import for logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__)

# 基础输出目录
os.makedirs(config.BASE_OUTPUT_DIR, exist_ok=True)

# 初始化Docker客户端
docker_client = docker.from_env()

# 用于存储执行ID和时间戳的字典及其锁
EXEC_DIR_TIMESTAMPS = {}
EXEC_DIR_TIMESTAMPS_LOCK = threading.Lock()

def is_code_safe(code):
    for pattern in config.FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            return False
    return True

def cleanup_dir(directory):
    logging.info(f"Attempting to clean up directory: {directory}")
    try:
        shutil.rmtree(directory)
        logging.info(f"Successfully cleaned up directory: {directory}")
    except Exception as e:
        logging.error(f"Error cleaning up directory {directory}: {e}")

def periodic_cleanup():
    logging.info("Periodic cleanup task started...")
    while True:
        try:
            time.sleep(300)  # 每5分钟检查一次
            
            current_time = time.time()
            ids_to_remove = []
            
            # Create a copy for safe iteration
            with EXEC_DIR_TIMESTAMPS_LOCK:
                timestamps_copy = dict(EXEC_DIR_TIMESTAMPS) 

            for exec_id, timestamp in timestamps_copy.items():
                age_seconds = current_time - timestamp
                current_exec_dir = os.path.join(config.BASE_OUTPUT_DIR, exec_id)
                logging.info(f"Checking directory {current_exec_dir} for cleanup (age: {age_seconds:.0f}s / TTL: {config.FILE_TTL_SECONDS}s)")
                if age_seconds > config.FILE_TTL_SECONDS:
                    logging.info(f"Directory {exec_id} has expired, preparing for cleanup.")
                    logging.info(f"Deleting directory {current_exec_dir} due to TTL expiry.")
                    try:
                        cleanup_dir(current_exec_dir) # cleanup_dir now has its own logging
                        ids_to_remove.append(exec_id)
                    except Exception as e:
                        logging.error(f"Error during periodic cleanup of directory {current_exec_dir}: {e}")
            
            if ids_to_remove:
                with EXEC_DIR_TIMESTAMPS_LOCK:
                    for exec_id in ids_to_remove:
                        if exec_id in EXEC_DIR_TIMESTAMPS:
                            del EXEC_DIR_TIMESTAMPS[exec_id]
                            logging.info(f"Removed {exec_id} from timestamp tracking after cleanup.")
            
            if not ids_to_remove:
                 logging.info("Periodic cleanup: No expired directories found.")
        except Exception as e:
            logging.error(f"Error in periodic_cleanup loop: {e}")


@app.route('/execute', methods=['POST'])
def execute_r_code():
    code = request.get_data(as_text=True)
    
    # 创建唯一的执行ID
    exec_id = uuid.uuid4().hex
    logging.info(f"Received execution request for exec_id: {exec_id}")

    # 安全检查
    if not is_code_safe(code):
        logging.warning(f"Unsafe code detected for exec_id: {exec_id}")
        return jsonify({'error': '代码中包含不允许的函数或模式'}), 400

    exec_dir = os.path.join(config.BASE_OUTPUT_DIR, exec_id)
    os.makedirs(exec_dir, exist_ok=True)

    script_filename = 'script.R'
    script_path = os.path.join(exec_dir, script_filename)

    with open(script_path, 'w') as f:
        f.write(code)

    try:
        container = docker_client.containers.run(
            config.R_EXECUTOR_IMAGE,
            command=script_filename,
            volumes={os.path.abspath(exec_dir): {'bind': '/home/ruser/code', 'mode': 'rw'}},
            working_dir='/home/ruser/code',
            network_disabled=True,
            detach=True,
            mem_limit=config.MEMORY_LIMIT,
            cpu_quota=int(config.CPU_LIMIT * 100000),
            stdout=True,
            stderr=True,
            remove=True,
            cap_drop=['ALL'],
            security_opt=["no-new-privileges"]
        )

        exit_status = container.wait(timeout=config.TIMEOUT)
        logs = container.logs(stdout=True, stderr=True).decode('utf-8')
        logging.info(f"Container for {exec_id} completed with status: {exit_status['StatusCode'] if isinstance(exit_status, dict) else exit_status}")


    except docker.errors.ContainerError as e:
        logs = e.stderr.decode('utf-8') if e.stderr else str(e)
        logging.error(f"Container error for {exec_id}: {logs}")
        return jsonify({'error': '代码执行出错', 'details': logs}), 400
    except docker.errors.ImageNotFound:
        logging.error(f"Docker image {config.R_EXECUTOR_IMAGE} not found for exec_id: {exec_id}")
        return jsonify({'error': f'Docker镜像 {config.R_EXECUTOR_IMAGE} 未找到'}), 500
    except docker.errors.APIError as e:
        logging.error(f"Docker API error during execution for {exec_id}: {str(e)}")
        return jsonify({'error': '执行代码时发生Docker API错误', 'details': str(e)}), 500
    except Exception as e:
        logging.error(f"Error during execution for {exec_id}: {str(e)}")
        return jsonify({'error': '执行代码时发生未知错误', 'details': str(e)}), 500

    generated_files = [f for f in os.listdir(exec_dir) if f != script_filename]
    file_urls = [request.host_url + 'files/' + exec_id + '/' + filename for filename in generated_files]

    with EXEC_DIR_TIMESTAMPS_LOCK:
        EXEC_DIR_TIMESTAMPS[exec_id] = time.time()
    logging.info(f"Execution {exec_id} completed. Output directory will be retained for {config.FILE_TTL_SECONDS / 60:.0f} minutes.")

    return jsonify({'output': logs, 'files': file_urls})

@app.route('/files/<exec_id>/<path:filename>', methods=['GET'])
def download_file(exec_id, filename):
    logging.info(f"Request for file {filename} in exec_id {exec_id}")

    if not re.match(r'^[a-zA-Z0-9]+$', exec_id):
        logging.warning(f"Invalid file download request: Invalid exec_id format. exec_id={exec_id}, filename={filename}")
        return jsonify({'error': 'Invalid execution ID format'}), 400

    if not re.match(r'^(?![\._-])[a-zA-Z0-9_.-]+(?<![\._-])$', filename) or \
       '..' in filename or \
       filename.startswith('/') or \
       filename.endswith('/'):
        logging.warning(f"Invalid file download request: Invalid filename format. exec_id={exec_id}, filename={filename}")
        return jsonify({'error': 'Invalid filename format'}), 400

    # This check is somewhat redundant due to above, but kept for clarity/defense-in-depth.
    if filename.startswith('/') or '..' in filename: 
        logging.warning(f"Invalid file download request: Path traversal attempt. exec_id={exec_id}, filename={filename}")
        return jsonify({'error': '无效的文件名'}), 400

    exec_dir = os.path.join(config.BASE_OUTPUT_DIR, exec_id)
    file_path = os.path.join(exec_dir, filename)

    if not os.path.isfile(file_path):
        logging.warning(f"File not found: {file_path}")
        return jsonify({'error': '文件未找到'}), 404

    return send_from_directory(exec_dir, filename, as_attachment=True)

if __name__ == '__main__':
    logging.info("Starting periodic cleanup thread...")
    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
    
    logging.info(f"Starting Flask app on host 0.0.0.0, port 8000")
    from waitress import serve
    serve(app, host='0.0.0.0', port=8000)
