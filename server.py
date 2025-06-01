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

# 获取当前脚本所在目录
SCRIPT_DIR = Path(__file__).parent.absolute()

# 脚本映射配置
SCRIPT_MAPPING = {
    'build_folder': 'Claude/Build_folder.py',
    'rename_files': 'Claude/Rename_files.py', 
    'webp_video': 'Claude/Webp_video_to_img.py',
    'copy_files': 'Claude/Copy_files.py',
    'unzip': 'Claude/Unzip.py',
    'md5_renew': 'Claude/Md5_renew.py',
    'auto_build_copy': 'Claude/Auto_build_and_copy.py',
    'webp_resize': 'Claude/Webp_resize.py'
}

class ToolboxRequestHandler(BaseHTTPRequestHandler):
    """
    处理Web请求的主要类
    
    支持的API端点:
    - GET /api/status: 获取服务器状态
    - POST /api/run-script: 执行指定的工具脚本
    - GET /: 返回主页面
    """
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/status':
            self._handle_status()
        elif parsed_path.path == '/' or parsed_path.path == '/index.html':
            self._serve_index_html()
        else:
            self._send_404()
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/run-script':
            self._handle_run_script()
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
            self._send_error_response(f"获取状态失败: {str(e)}")
    
    def _handle_run_script(self):
        """处理脚本执行请求"""
        try:
            # 读取请求数据
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            script_name = request_data.get('script')
            params = request_data.get('params', {})
            
            # 验证脚本名称
            if script_name not in SCRIPT_MAPPING:
                self._send_error_response(f"未知的脚本: {script_name}")
                return
            
            # 获取脚本文件路径
            script_file = SCRIPT_DIR / SCRIPT_MAPPING[script_name]
            if not script_file.exists():
                self._send_error_response(f"脚本文件不存在: {script_file}")
                return
            
            # 执行脚本
            self._execute_script(script_file, script_name, params)
            
        except json.JSONDecodeError:
            self._send_error_response("无效的JSON数据")
        except Exception as e:
            self._send_error_response(f"处理请求失败: {str(e)}")
    
    def _execute_script(self, script_file: Path, script_name: str, params: dict):
        """执行Python脚本并流式返回输出"""
        try:
            # 设置响应头
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Transfer-Encoding', 'chunked')
            self.end_headers()
            
            # 准备脚本输入
            script_input = self._prepare_script_input(script_name, params)
            
            # 发送开始信息
            self._send_stream_data({
                'type': 'output',
                'content': f"=== 开始执行 {SCRIPT_MAPPING[script_name]} ==="
            })
            
            self._send_stream_data({
                'type': 'output', 
                'content': f"参数: {json.dumps(params, ensure_ascii=False, indent=2)}"
            })
            
            # 执行脚本
            process = subprocess.Popen(
                [sys.executable, str(script_file)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                cwd=str(SCRIPT_DIR),
                bufsize=1,
                universal_newlines=True
            )
            
            # 发送输入到脚本
            if script_input:
                try:
                    process.stdin.write(script_input)
                    process.stdin.flush()
                    process.stdin.close()
                except Exception as e:
                    self._send_stream_data({
                        'type': 'error',
                        'content': f"发送输入到脚本失败: {str(e)}"
                    })
            
            # 实时读取输出
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self._send_stream_data({
                        'type': 'output',
                        'content': output.rstrip()
                    })
            
            # 等待进程结束
            return_code = process.wait()
            
            # 发送结束信息
            if return_code == 0:
                self._send_stream_data({
                    'type': 'success',
                    'content': f"=== 脚本执行完成，返回码: {return_code} ==="
                })
            else:
                self._send_stream_data({
                    'type': 'error',
                    'content': f"=== 脚本执行失败，返回码: {return_code} ==="
                })
                
        except Exception as e:
            self._send_stream_data({
                'type': 'error',
                'content': f"执行脚本时发生错误: {str(e)}"
            })
    
    def _prepare_script_input(self, script_name: str, params: dict) -> str:
        """根据脚本类型和参数准备输入数据"""
        inputs = []
        
        if script_name == 'build_folder':
            inputs.append(params.get('path', ''))
            inputs.append(str(params.get('count', 5)))
            
        elif script_name == 'rename_files':
            inputs.append(params.get('path', ''))
            
        elif script_name == 'webp_video':
            inputs.append(params.get('path', ''))
            # 对于覆盖选项，如果为True则输入'y'，否则输入'n'
            if params.get('overwrite', False):
                inputs.append('y')
            else:
                inputs.append('n')
                
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
            
        elif script_name == 'auto_build_copy':
            inputs.append(params.get('base_path', ''))
            inputs.append(str(params.get('count', 5)))
            inputs.append(params.get('source_path', ''))
            
        elif script_name == 'webp_resize':
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

def signal_handler(signum, frame):
    """信号处理函数，用于优雅退出"""
    print("\n\n=== 收到退出信号，正在关闭服务器... ===")
    print("感谢使用小红书工具箱！")
    sys.exit(0)

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
        server.serve_forever()
        
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