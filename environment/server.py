#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书工具箱 Web 服务器

功能说明:
本脚本提供一个简单的Web服务器，用于通过Web界面调用项目中的各种Python工具脚本。
支持实时输出显示，让用户能够看到脚本执行的详细过程。

主要特性:
- 提供RESTful API接口调用各种工具脚本
- 实时流式输出脚本执行结果
- 支持所有项目中的工具脚本
- 自动参数验证和错误处理
- 跨域支持，便于开发调试
- 异步执行和多线程支持，确保停止命令及时响应

使用方法:
1. 运行此脚本: python server.py
2. 在浏览器中打开 index.html 文件
3. 通过Web界面使用各种工具

注意事项:
- 确保所有依赖的Python脚本都在同一目录下
- 服务器默认运行在 http://localhost:8000
- 支持用户中断操作（Ctrl+C）优雅退出
"""

import os
import sys
import json
import subprocess
import threading
import time
import platform
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import queue
import signal
import uuid
from concurrent.futures import ThreadPoolExecutor
import asyncio
from typing import Dict, Optional

# 获取项目根目录（server.py现在在environment文件夹中）
SCRIPT_DIR = Path(__file__).resolve().parent.parent

# 脚本映射配置
SCRIPT_MAPPING = {
    'build_folder': 'Claude/Build_folder.py',
    'rename_files': 'Claude/Rename_files.py', 
    'webp_video': 'Claude/Webp_video_to_img.py',
    'copy_files': 'Claude/Copy_files.py',
    'unzip': 'Claude/Unzip.py',
    'md5_renew': 'Claude/Md5_renew.py',
    'auto_build_copy': 'Claude/Auto_build_and_copy.py',
    'webp_resize': 'Claude/Webp_resize.py',
    'excel_renew': 'Claude/Excel_renew.py',
    'test_stop_button': 'Claude/Test_stop_button.py'
}

# 全局变量，用于存储当前运行的进程和任务管理
current_processes: Dict[str, subprocess.Popen] = {}
active_tasks: Dict[str, dict] = {}
process_lock = threading.Lock()
task_executor = ThreadPoolExecutor(max_workers=5)  # 创建线程池

class ToolboxRequestHandler(BaseHTTPRequestHandler):
    """
    处理Web请求的主要类
    
    支持的API端点:
    - GET /: 返回主页面
    - POST /api/run-script: 执行指定的Python脚本
    - POST /api/stop-script: 终止当前执行的脚本
    - GET /environment/*: 提供静态文件（CSS、JS等）
    
    所有响应都支持跨域访问，便于开发调试。
    """
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/status':
            self._handle_status()
        elif parsed_path.path == '/api/tasks':
            self._handle_get_tasks()
        elif parsed_path.path == '/' or parsed_path.path == '/index.html':
            self._serve_index_html()
        elif parsed_path.path.startswith('/environment/'):
            self._serve_static_file(parsed_path.path)
        else:
            self._send_404()
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/run-script':
            self._handle_run_script()
        elif parsed_path.path == '/api/stop-script':
            self._handle_stop_script()
        elif parsed_path.path == '/api/restart-server':
            self._handle_restart_server()
        elif parsed_path.path == '/api/shutdown-server':
            self._handle_shutdown_server()
        else:
            self._send_404()
    
    def _handle_status(self):
        """处理状态查询请求"""
        try:
            status_data = {
                'status': 'ok',
                'message': '小红书工具箱服务器运行正常',
                'working_directory': str(SCRIPT_DIR),
                'python_version': platform.python_version(),
                'available_scripts': list(SCRIPT_MAPPING.keys())
            }
            
            self._send_json_response(status_data)
            
        except Exception as e:
            self._send_error_response(f"处理脚本执行请求失败: {str(e)}")
    
    def _handle_get_tasks(self):
        """处理获取活动任务列表请求"""
        try:
            with process_lock:
                tasks_info = []
                for task_id, task_data in active_tasks.items():
                    task_info = {
                        'task_id': task_id,
                        'script_name': task_data.get('script_name'),
                        'status': task_data.get('status'),
                        'start_time': task_data.get('start_time'),
                        'elapsed_time': time.time() - task_data.get('start_time', time.time())
                    }
                    if 'error' in task_data:
                        task_info['error'] = task_data['error']
                    if 'return_code' in task_data:
                        task_info['return_code'] = task_data['return_code']
                    tasks_info.append(task_info)
                
                response_data = {
                    'active_tasks': tasks_info,
                    'process_count': len(current_processes),
                    'total_tasks': len(active_tasks)
                }
                
                self._send_json_response(response_data)
                
        except Exception as e:
            self._send_error_response(f"获取任务列表失败: {str(e)}")
    
    def _handle_stop_script(self):
        """处理终止脚本请求"""
        global current_processes
        try:
            with process_lock:
                print(f"终止请求 - current_processes: {list(current_processes.keys())}")
                print(f"终止请求 - active_tasks: {list(active_tasks.keys())}")
                
                if current_processes:
                    stopped_processes = []
                    
                    for pid, process in list(current_processes.items()):
                        if process.poll() is None:  # 进程仍在运行
                            print(f"正在强制终止进程 PID: {pid}")
                            
                            try:
                                if platform.system() == "Windows":
                                    # Windows系统：直接使用强制终止
                                    print(f"使用taskkill强制终止进程树 PID: {pid}")
                                    result = subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], 
                                                          capture_output=True, text=True, timeout=3)
                                    if result.returncode == 0:
                                        print(f"进程树已强制终止 PID: {pid}")
                                        stopped_processes.append(pid)
                                    else:
                                        print(f"taskkill失败: {result.stderr}，尝试Python方法 PID: {pid}")
                                        process.kill()
                                        try:
                                            process.wait(timeout=2)
                                            stopped_processes.append(pid)
                                        except subprocess.TimeoutExpired:
                                            print(f"进程可能已经终止 PID: {pid}")
                                            stopped_processes.append(pid)
                                else:
                                    # Unix系统：直接强制杀死
                                    print(f"强制终止进程 PID: {pid}")
                                    process.kill()
                                    process.wait(timeout=2)
                                    stopped_processes.append(pid)
                                    print(f"进程已强制终止 PID: {pid}")
                                    
                            except Exception as e:
                                print(f"终止进程失败 PID: {pid}, 错误: {e}")
                                # 即使失败也标记为已处理
                                stopped_processes.append(pid)
                    
                    # 清理所有进程引用
                    current_processes.clear()
                    
                    # 清理所有任务
                    active_tasks.clear()
                    
                    if stopped_processes:
                        self._send_json_response({
                            'status': 'success',
                            'message': f'已强制终止 {len(stopped_processes)} 个脚本进程'
                        })
                    else:
                        self._send_json_response({
                            'status': 'info',
                            'message': '没有发现正在运行的脚本进程'
                        })
                else:
                    self._send_json_response({
                        'status': 'info',
                        'message': '当前没有通过Web界面启动的脚本'
                    })
                    
        except Exception as e:
            print(f"终止脚本异常: {e}")
            self._send_error_response(f"终止脚本失败: {str(e)}")
    
    def _handle_restart_server(self):
        """处理服务器重启请求"""
        try:
            self._send_json_response({
                'status': 'success',
                'message': '服务器重启功能已收到请求，但需要外部工具支持'
            })
            
            # 注意：这里只是返回成功响应，实际重启需要外部脚本
            # 可以在这里添加调用外部重启脚本的逻辑
            print("收到服务器重启请求")
            
        except Exception as e:
            self._send_error_response(f"处理重启请求失败: {str(e)}")
    
    def _handle_shutdown_server(self):
        """处理服务器停止请求"""
        try:
            # 先发送响应
            self._send_json_response({
                'status': 'success',
                'message': '服务器即将关闭'
            })
            
            print("收到服务器停止请求，即将关闭...")
            
            # 在单独的线程中延迟关闭服务器，确保响应能够发送
            import threading
            def delayed_shutdown():
                import time
                time.sleep(1)  # 等待1秒确保响应发送完成
                global server_should_exit
                server_should_exit = True
                print("服务器正在关闭...")
            
            shutdown_thread = threading.Thread(target=delayed_shutdown)
            shutdown_thread.daemon = True
            shutdown_thread.start()
            
        except Exception as e:
            self._send_error_response(f"处理停止请求失败: {str(e)}")
    
    def _handle_run_script(self):
        """处理脚本执行请求 - 异步版本"""
        try:
            # 读取请求数据
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # 解析FormData
            import cgi
            from io import BytesIO
            
            # 创建一个模拟的文件对象
            fp = BytesIO(post_data)
            
            # 解析multipart/form-data
            form = cgi.FieldStorage(
                fp=fp,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )
            
            # 获取脚本名称
            script_name = form.getvalue('script')
            
            # 获取所有参数
            params = {}
            for key in form.keys():
                if key != 'script':
                    params[key] = form.getvalue(key)
            
            # 验证脚本名称
            if not script_name or script_name not in SCRIPT_MAPPING:
                self._send_error_response(f"无效的脚本名称: {script_name}")
                return
            
            # 获取脚本文件路径
            script_file = SCRIPT_DIR / SCRIPT_MAPPING[script_name]
            
            if not script_file.exists():
                self._send_error_response(f"脚本文件不存在: {script_file}")
                return
            
            # 生成任务ID
            task_id = str(uuid.uuid4())[:8]
            
            # 记录任务信息
            with process_lock:
                active_tasks[task_id] = {
                    'script_name': script_name,
                    'params': params,
                    'start_time': time.time(),
                    'status': 'starting'
                }
            
            # 设置响应头（立即开始流式响应）
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Transfer-Encoding', 'chunked')
            self.end_headers()
            
            # 发送任务开始信息
            self._send_stream_data({
                'type': 'output',
                'content': f"=== 任务开始 [{task_id}] {Path(SCRIPT_MAPPING[script_name]).name} ==="
            })
            
            # 在线程池中异步执行脚本
            future = task_executor.submit(
                self._execute_script_async, 
                script_file, 
                script_name, 
                params, 
                task_id
            )
            
            # 在主线程中监控执行状态并发送实时输出
            self._monitor_script_execution(future, task_id)
            
        except Exception as e:
            self._send_stream_error(f"处理请求失败: {str(e)}")
    
    def _execute_script_async(self, script_file: Path, script_name: str, params: dict, task_id: str):
        """在独立线程中异步执行Python脚本"""
        global current_processes
        
        try:
            # 更新任务状态
            with process_lock:
                if task_id in active_tasks:
                    active_tasks[task_id]['status'] = 'running'
            
            # 准备脚本输入
            script_input_result = self._prepare_script_input(script_name, params)
            
            # 处理不同类型的脚本输入
            if isinstance(script_input_result, tuple) and len(script_input_result) == 2:
                script_input, cmd_args = script_input_result
                cmd = [sys.executable, '-u', str(script_file)] + cmd_args
                print(f"[DEBUG] 使用命令行参数模式: {cmd}")
            else:
                script_input = script_input_result
                cmd = [sys.executable, '-u', str(script_file)]
                print(f"[DEBUG] 使用标准输入模式: {cmd}")
                print(f"[DEBUG] 标准输入内容: {repr(script_input)}")
            
            # 设置环境变量
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUNBUFFERED'] = '1'
            env['WEBP_TOOL_SERVER_MODE'] = '1'  # 标识服务器模式
            
            script_cwd = script_file.parent
            
            # 根据操作系统设置进程创建参数
            if platform.system() == "Windows":
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    cwd=str(script_cwd),
                    bufsize=0,  # 无缓冲
                    universal_newlines=True,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    cwd=str(script_cwd),
                    bufsize=0,  # 无缓冲
                    universal_newlines=True,
                    env=env,
                    preexec_fn=os.setsid
                )
            
            # 存储进程引用
            with process_lock:
                current_processes[str(process.pid)] = process
            
            print(f"[DEBUG] 脚本进程已启动，PID: {process.pid}")
            
            # 发送输入到脚本
            if script_input:
                try:
                    process.stdin.write(script_input)
                    process.stdin.flush()
                    process.stdin.close()
                    print(f"[DEBUG] 已发送输入到脚本")
                except Exception as e:
                    print(f"[DEBUG] 发送输入到脚本失败: {str(e)}")
            else:
                # 如果没有输入，也关闭stdin避免脚本等待
                try:
                    process.stdin.close()
                    print(f"[DEBUG] 已关闭stdin（无输入）")
                except Exception as e:
                    print(f"[DEBUG] 关闭stdin失败: {str(e)}")
            
            # 使用实时输出读取 - 直接返回进程对象供监控使用
            return {
                'process': process,
                'task_id': task_id,
                'script_name': script_name
            }
            
        except Exception as e:
            # 清理进程引用
            with process_lock:
                if 'process' in locals():
                    current_processes.pop(str(process.pid), None)
                if task_id in active_tasks:
                    active_tasks[task_id]['status'] = 'failed'
                    active_tasks[task_id]['error'] = str(e)
            
            print(f"[DEBUG] 执行脚本时发生错误: {str(e)}")
            return {
                'error': str(e),
                'task_id': task_id
            }
    
    def _monitor_script_execution(self, future, task_id: str):
        """监控脚本执行状态并发送实时输出"""
        process = None
        try:
            # 等待脚本启动
            print(f"[DEBUG] 开始监控任务 {task_id}")
            
            # 获取执行结果
            result = future.result(timeout=10.0)  # 等待脚本启动
            
            if 'error' in result:
                self._send_stream_data({
                    'type': 'error',
                    'content': f"启动脚本失败: {result['error']}"
                })
                return
            
            process = result['process']
            script_name = result['script_name']
            
            print(f"[DEBUG] 获取到进程对象，开始实时读取输出，PID: {process.pid}")
            
            # 实时读取输出并发送
            output_count = 0
            connection_broken = False
            
            while True:
                # *** 第一优先级：检查连接是否已断开 ***
                if connection_broken:
                    print(f"[DEBUG] 连接已断开，立即终止脚本进程 PID: {process.pid}")
                    self._terminate_process(process, f"连接断开，强制终止任务 {task_id}")
                    break
                
                # 检查进程是否仍在运行
                if process.poll() is not None:
                    # 进程已结束，读取剩余输出
                    remaining_output = process.stdout.read()
                    if remaining_output and not connection_broken:
                        for line in remaining_output.splitlines():
                            if line.strip():
                                try:
                                    self._send_stream_data({
                                        'type': 'output',
                                        'content': line.strip()
                                    })
                                    output_count += 1
                                except Exception as e:
                                    print(f"[DEBUG] 发送剩余输出失败，连接已断开: {e}")
                                    connection_broken = True
                                    break
                    break
                
                # 读取一行输出
                try:
                    output_line = process.stdout.readline()
                    if output_line:
                        output_count += 1
                        try:
                            self._send_stream_data({
                                'type': 'output',
                                'content': output_line.rstrip()
                            })
                            print(f"[DEBUG] 发送输出行 {output_count}: {output_line.rstrip()[:50]}...")
                        except Exception as send_error:
                            print(f"[DEBUG] 发送数据失败，连接断开，设置断开标记: {send_error}")
                            connection_broken = True
                            # 不要continue，让下次循环开始时检查connection_broken状态
                    elif not output_line:
                        # 没有更多输出，测试连接状态
                        if not connection_broken:
                            try:
                                # 发送一个心跳测试连接
                                self._send_stream_data({
                                    'type': 'ping',
                                    'content': ''
                                })
                            except Exception as ping_error:
                                print(f"[DEBUG] 心跳检测失败，连接已断开: {ping_error}")
                                connection_broken = True
                        
                        # 没有更多输出，稍等片刻
                        time.sleep(0.1)
                except Exception as e:
                    print(f"[DEBUG] 读取输出时出错: {e}")
                    if not connection_broken:
                        try:
                            self._send_stream_data({
                                'type': 'error',
                                'content': f"读取输出时发生错误: {str(e)}"
                            })
                        except:
                            print(f"[DEBUG] 发送错误信息失败，连接已断开")
                            connection_broken = True
                    break
            
            # 获取返回码
            if process.poll() is not None:
                return_code = process.returncode
                if connection_broken:
                    print(f"[DEBUG] 脚本因连接断开被终止，返回码: {return_code}，总输出行数: {output_count}")
                else:
                    print(f"[DEBUG] 脚本执行完成，返回码: {return_code}，总输出行数: {output_count}")
            else:
                # 进程可能被强制终止
                return_code = -1
                print(f"[DEBUG] 脚本被强制终止，总输出行数: {output_count}")
            
            # 清理进程引用
            with process_lock:
                current_processes.pop(str(process.pid), None)
                if task_id in active_tasks:
                    if connection_broken:
                        active_tasks[task_id]['status'] = 'terminated'
                    else:
                        active_tasks[task_id]['status'] = 'completed'
                    active_tasks[task_id]['return_code'] = return_code
            
            # 只有在连接未断开时才发送结束信息
            if not connection_broken:
                # 发送结束信息
                if return_code == 0:
                    self._send_stream_data({
                        'type': 'success',
                        'content': f"=== 任务 [{task_id}] 执行完成，返回码: {return_code} ==="
                    })
                elif return_code == -15 or return_code == 1:
                    self._send_stream_data({
                        'type': 'warning',
                        'content': f"=== 任务 [{task_id}] 被用户终止 ==="
                    })
                else:
                    self._send_stream_data({
                        'type': 'error',
                        'content': f"=== 任务 [{task_id}] 执行失败，返回码: {return_code} ==="
                    })
                
                # 发送结束标记
                self._send_stream_data({
                    'type': 'end',
                    'content': 'STREAM_END'
                })
            else:
                print(f"[DEBUG] 连接已断开，跳过发送结束信息")
            
        except Exception as e:
            print(f"[DEBUG] 监控任务执行时发生错误: {str(e)}")
            # 如果有进程在运行，尝试终止它
            if process and process.poll() is None:
                self._terminate_process(process, f"监控异常，终止任务 {task_id}")
            
            try:
                self._send_stream_data({
                    'type': 'error',
                    'content': f"监控任务执行时发生错误: {str(e)}"
                })
            except:
                print(f"[DEBUG] 无法发送错误信息，连接可能已断开")
        finally:
            # 清理任务记录
            with process_lock:
                active_tasks.pop(task_id, None)
            print(f"[DEBUG] 任务 {task_id} 监控结束")
    
    def _prepare_script_input(self, script_name: str, params: dict) -> str:
        """根据脚本类型和参数准备输入数据"""
        inputs = []
        
        if script_name == 'build_folder':
            inputs.append(params.get('path', ''))
            inputs.append(str(params.get('count', 5)))
            
        elif script_name == 'rename_files':
            inputs.append(params.get('path', ''))
            
        elif script_name == 'webp_video':
            folder_path = params.get('path')  # 修正参数名称
            overwrite_value = params.get('overwrite', 'false') # 默认为 'false'
            duration_value = params.get('duration', '3')

            # 转换 overwrite 参数为脚本期望的命令行选项值
            if isinstance(overwrite_value, bool):
                actual_overwrite_mode = 'replace_all' if overwrite_value else 'skip'
            elif isinstance(overwrite_value, str):
                if overwrite_value.lower() in ['true', 'y', 'yes', '1', 'replace_all']:
                    actual_overwrite_mode = 'replace_all'
                else:
                    actual_overwrite_mode = 'skip'
            else:
                actual_overwrite_mode = 'skip' # 默认跳过

            # 准备命令行参数
            # 第一个参数是必须的 root_folder
            # 后续是可选参数 --overwrite 和 --duration
            prepared_args = [
                str(folder_path), # root_folder
                '--overwrite', str(actual_overwrite_mode),
                '--duration', str(duration_value)
            ]
            return [], prepared_args # 没有标准输入，只有命令行参数
                
        elif script_name == 'copy_files':
            inputs.append(params.get('source_path', ''))
            inputs.append(params.get('target_path', ''))
            
        elif script_name == 'unzip':
            inputs.append(params.get('path', ''))
            if params.get('overwrite', False):
                inputs.append('y')
            else:
                inputs.append('n')
                
        elif script_name == 'md5_renew':
            inputs.append(params.get('path', ''))
            inputs.append(str(params.get('bytes', 10)))
            
        elif script_name == 'auto_build_copy':
            inputs.append(params.get('base_path', ''))
            inputs.append(str(params.get('count', 5)))
            inputs.append(params.get('source_path', ''))
            
        elif script_name == 'webp_resize':
            inputs.append(params.get('path', ''))
            inputs.append(str(params.get('size_threshold', 10)))  # 默认10MB
            inputs.append(str(params.get('fps', 15)))  # 默认15fps
            
        elif script_name == 'excel_renew':
            inputs.append(params.get('path', ''))
            
        # 添加换行符
        return '\n'.join(inputs) + '\n' if inputs else ''
    
    def _send_stream_data(self, data: dict):
        """发送流式数据"""
        try:
            json_data = json.dumps(data, ensure_ascii=False) + '\n'
            data_bytes = json_data.encode('utf-8')
            
            # 发送chunk大小（十六进制）
            chunk_size = hex(len(data_bytes))[2:].encode('ascii')
            self.wfile.write(chunk_size + b'\r\n')
            
            # 发送数据
            self.wfile.write(data_bytes + b'\r\n')
            self.wfile.flush()
            
        except Exception as e:
            print(f"发送流式数据失败: {e}")
    
    def _serve_index_html(self):
        """提供主页面"""
        try:
            index_file = SCRIPT_DIR / 'index.html'
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            else:
                self._send_404()
        except Exception as e:
            self._send_error_response(f"读取主页面失败: {str(e)}")
    
    def _serve_static_file(self, path: str):
        """提供静态文件（CSS、JS等）"""
        try:
            # 移除开头的斜杠，构建相对于项目根目录的路径
            relative_path = path.lstrip('/')
            static_file = SCRIPT_DIR / relative_path
            
            if static_file.exists() and static_file.is_file():
                # 根据文件扩展名确定Content-Type
                content_type = 'text/plain'
                if path.endswith('.css'):
                    content_type = 'text/css; charset=utf-8'
                elif path.endswith('.js'):
                    content_type = 'application/javascript; charset=utf-8'
                elif path.endswith('.html'):
                    content_type = 'text/html; charset=utf-8'
                elif path.endswith('.json'):
                    content_type = 'application/json; charset=utf-8'
                
                with open(static_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            else:
                self._send_404()
        except Exception as e:
            self._send_error_response(f"读取静态文件失败: {str(e)}")
    
    def _send_json_response(self, data: dict, status_code: int = 200):
        """发送JSON响应"""
        try:
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            
            self.send_response(status_code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            self.wfile.write(json_data.encode('utf-8'))
        except Exception as e:
            print(f"发送JSON响应失败: {e}")
    
    def _send_stream_error(self, message: str):
        """发送流式错误响应"""
        try:
            # 设置响应头
            self.send_response(200)  # 使用200状态码，错误信息在流中传递
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Transfer-Encoding', 'chunked')
            self.end_headers()
            
            # 发送错误信息
            self._send_stream_data({
                'type': 'error',
                'content': message
            })
        except Exception as e:
            print(f"发送流式错误响应失败: {e}")
    
    def _send_error_response(self, message: str, status_code: int = 500):
        """发送错误响应"""
        error_data = {
            'error': True,
            'message': message,
            'timestamp': time.time()
        }
        self._send_json_response(error_data, status_code)
    
    def _send_404(self):
        """发送404响应"""
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write('404 Not Found'.encode('utf-8'))
    
    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {format % args}")

    def _terminate_process(self, process, reason: str):
        """安全地终止进程"""
        try:
            if process and process.poll() is None:
                print(f"[DEBUG] {reason}，正在终止进程 PID: {process.pid}")
                
                if platform.system() == "Windows":
                    # Windows系统：直接使用强制终止，不再尝试优雅终止
                    try:
                        print(f"[DEBUG] 立即强制终止进程树 PID: {process.pid}")
                        result = subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], 
                                              capture_output=True, text=True, timeout=3)
                        if result.returncode == 0:
                            print(f"[DEBUG] 进程树已强制终止 PID: {process.pid}")
                        else:
                            print(f"[DEBUG] taskkill失败: {result.stderr}，尝试Python方法 PID: {process.pid}")
                            process.kill()
                            try:
                                process.wait(timeout=1)
                                print(f"[DEBUG] Python方法终止成功 PID: {process.pid}")
                            except subprocess.TimeoutExpired:
                                print(f"[DEBUG] 进程终止超时，但已发送终止信号 PID: {process.pid}")
                    except Exception as e:
                        print(f"[DEBUG] 强制终止失败，尝试最后手段: {e}")
                        try:
                            process.kill()
                            process.wait(timeout=1)
                        except:
                            print(f"[DEBUG] 所有终止方法都失败，进程可能已终止 PID: {process.pid}")
                else:
                    # Unix系统：直接使用强制终止
                    try:
                        process.kill()
                        process.wait(timeout=2)
                        print(f"[DEBUG] 进程已强制终止 PID: {process.pid}")
                    except subprocess.TimeoutExpired:
                        print(f"[DEBUG] 进程终止超时，但已发送终止信号 PID: {process.pid}")
                
                # 从进程字典中移除
                with process_lock:
                    current_processes.pop(str(process.pid), None)
                    print(f"[DEBUG] 已从进程字典中移除 PID: {process.pid}")
                    
        except Exception as e:
            print(f"[DEBUG] 终止进程时发生错误: {e}")
            # 即使出错也要清理进程引用
            try:
                with process_lock:
                    current_processes.pop(str(process.pid), None)
            except:
                pass

# 全局退出标志
server_should_exit = False

def signal_handler(signum, frame):
    """信号处理函数，用于优雅退出"""
    global server_should_exit
    print("\n\n=== 收到退出信号，正在关闭服务器... ===")
    print("感谢使用小红书工具箱！")
    server_should_exit = True

def check_dependencies():
    """检查依赖的脚本文件是否存在"""
    print("=== 检查依赖文件 ===")
    missing_files = []
    
    for script_key, script_file in SCRIPT_MAPPING.items():
        file_path = SCRIPT_DIR / script_file
        if file_path.exists():
            print(f"✅ {script_file}")
        else:
            print(f"❌ {script_file} (缺失)")
            missing_files.append(script_file)
    
    if missing_files:
        print(f"\n⚠️  警告: 发现 {len(missing_files)} 个缺失的脚本文件")
        print("某些功能可能无法正常使用")
    else:
        print("\n✅ 所有依赖文件检查完成")
    
    return len(missing_files) == 0

def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    print("="*60)
    print("🛠️  小红书工具箱 Web 服务器")
    print("="*60)
    print(f"📁 工作目录: {SCRIPT_DIR}")
    print(f"🐍 Python版本: {platform.python_version()}")
    print(f"💻 操作系统: {platform.system()} {platform.release()}")
    print()
    
    # 检查依赖文件
    check_dependencies()
    print()
    
    # 服务器配置
    HOST = 'localhost'
    PORT = 8000
    
    try:
        # 创建HTTP服务器
        server = HTTPServer((HOST, PORT), ToolboxRequestHandler)
        
        print(f"🚀 服务器启动成功!")
        print(f"📡 服务地址: http://{HOST}:{PORT}")
        print(f"🌐 Web界面: http://{HOST}:{PORT}/")
        print()
        print("💡 使用说明:")
        print("   1. 在浏览器中打开上述Web界面地址")
        print("   2. 选择需要使用的工具")
        print("   3. 填写相应参数后点击执行")
        print()
        print("⚠️  注意: 按 Ctrl+C 可以安全退出服务器")
        print("="*60)
        print()
        
        # 启动服务器
        # 使用循环检查退出标志，而不是直接serve_forever()
        while not server_should_exit:
            try:
                server.handle_request()
            except KeyboardInterrupt:
                break
            except Exception as e:
                if not server_should_exit:
                    print(f"处理请求时发生错误: {e}")
        
        # 关闭服务器
        server.server_close()
        
    except OSError as e:
        if e.errno == 10048:  # Windows: Address already in use
            print(f"❌ 端口 {PORT} 已被占用")
            print("请检查是否已有服务器在运行，或尝试使用其他端口")
        else:
            print(f"❌ 启动服务器失败: {e}")
    except KeyboardInterrupt:
        print("\n\n=== 用户中断，正在关闭服务器... ===")
    except Exception as e:
        print(f"❌ 服务器运行时发生错误: {e}")
    finally:
        print("\n🔚 服务器已关闭")
        print("感谢使用小红书工具箱！")

if __name__ == '__main__':
    main()