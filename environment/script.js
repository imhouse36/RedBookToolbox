// 全局变量
let currentProcess = null;
let isScriptRunning = false;
let abortController = null;

// 脚本名称映射，用于显示友好的脚本名称
const SCRIPT_DISPLAY_NAMES = {
    'build_folder': 'Build_folder.py',
    'rename_files': 'Rename_files.py',
    'webp_video': 'Webp_video_to_img.py',
    'copy_files': 'Copy_files.py',
    'unzip': 'Unzip.py',
    'md5_renew': 'Md5_renew.py',
    'auto_build_copy': 'Auto_build_and_copy.py',
    'webp_resize': 'Webp_resize.py',
    'excel_renew': 'Excel_renew.py',
    'test_stop_button': 'Test_stop_button.py'
};

// 终止脚本函数 - 全局作用域
async function stopScript() {
    try {
        console.log('用户请求终止脚本');
        
        // 如果有正在进行的请求，先尝试取消
        if (abortController) {
            console.log('取消当前fetch请求');
            abortController.abort();
            abortController = null;
        }
        
        // 立即调用服务器停止API
        console.log('调用服务器停止API');
        const response = await fetch('/api/stop-script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({})
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('服务器停止响应:', result);
        
        // 显示终止结果
        const outputContent = document.getElementById('output-content');
        if (result.status === 'success') {
            if (typeof appendOutput === 'function') {
                appendOutput(`=== ${result.message} ===`, 'warning');
            } else {
                outputContent.innerHTML += `<div class="output-line warning">🟡 === ${result.message} ===</div>`;
            }
        } else if (result.status === 'info') {
            if (typeof appendOutput === 'function') {
                appendOutput(result.message, 'info');
            } else {
                outputContent.innerHTML += `<div class="output-line info">ℹ️ ${result.message}</div>`;
            }
        }
        
        // 重置UI状态
        resetUIState();
        
    } catch (error) {
        console.error('终止脚本失败:', error);
        
        // 如果是请求被取消，不显示错误
        if (error.name === 'AbortError') {
            console.log('停止请求被取消');
            return;
        }
        
        // 提供更详细的错误信息
        let errorMessage = '终止脚本失败';
        if (error.message) {
            errorMessage += `: ${error.message}`;
        }
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            errorMessage += ' (网络连接失败，请检查服务器是否正常运行)';
        }
        
        // 显示错误信息
        if (typeof appendOutput === 'function') {
            appendOutput(errorMessage, 'error');
        } else {
            const outputContent = document.getElementById('output-content');
            outputContent.innerHTML += `<div class="output-line error">❌ ${errorMessage}</div>`;
        }
        
        // 即使出错也重置UI状态
        resetUIState();
    }
}

// 重置UI状态的辅助函数
function resetUIState() {
    isScriptRunning = false;
    abortController = null;
    
    // 停止任务监控
    stopTaskMonitoring();
    
    // 更新UI状态
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-indicator span');
    const stopButton = document.getElementById('stop-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    if (statusDot) statusDot.className = 'status-dot';
    if (statusText) statusText.textContent = '就绪';
    if (stopButton) stopButton.style.display = 'none';
    if (loadingOverlay) loadingOverlay.classList.remove('show');
    
    // 重置所有执行按钮
    const runButtons = document.querySelectorAll('.execute-btn');
    runButtons.forEach(button => {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-play"></i> 开始执行';
    });
    
    // 隐藏所有内联终止按钮
    const inlineStopButtons = document.querySelectorAll('.stop-btn-inline');
    inlineStopButtons.forEach(button => {
        button.style.display = 'none';
    });
    
    console.log('UI状态已重置，任务监控已停止');
}

// 运行脚本函数 - 改进的异步版本
async function runScript(scriptName, toolItem) {
    // 防止重复执行
    if (isScriptRunning) {
        appendOutput('⚠️ 已有脚本正在执行，请先停止当前脚本', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('script', scriptName);
    
    // 获取工具项中的所有输入参数
    const inputs = toolItem.querySelectorAll('input, select');
    inputs.forEach(input => {
        if (input.value.trim()) {
            formData.append(input.name, input.value.trim());
        }
    });
    
    // 更新执行状态
    isScriptRunning = true;
    
    // 创建新的AbortController
    abortController = new AbortController();
    
    // 显示加载状态
    const loadingOverlay = document.getElementById('loading-overlay');
    const outputContent = document.getElementById('output-content');
    const runButton = toolItem.querySelector('.execute-btn');
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-indicator span');
    const stopButton = document.getElementById('stop-btn');
    
    // 更新状态
    loadingOverlay.classList.add('show');
    outputContent.innerHTML = '';
    runButton.disabled = true;
    runButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 执行中...';
    statusDot.className = 'status-dot running';
    statusText.textContent = '正在执行';
    stopButton.style.display = 'flex'; // 显示全局终止按钮
    
    // 显示当前工具的内联终止按钮
    const inlineStopButton = toolItem.querySelector('.stop-btn-inline');
    if (inlineStopButton) {
        inlineStopButton.style.display = 'flex';
    }
    
    try {
        appendOutput(`🚀 开始执行脚本: ${SCRIPT_DISPLAY_NAMES[scriptName]}`, 'info');
        
        // 启动任务监控
        startTaskMonitoring();
        
        const response = await fetch('/api/run-script', {
            method: 'POST',
            body: formData,
            signal: abortController.signal  // 添加取消信号
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        // 一旦开始接收数据流，立即隐藏loading overlay以显示实时输出
        loadingOverlay.classList.remove('show');
        
        // 使用异步循环读取流数据
        while (true) {
            // 检查是否被取消
            if (abortController.signal.aborted) {
                break;
            }
            
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            
            // 简化处理：直接按行分割处理JSON数据
            const lines = buffer.split('\n');
            buffer = lines.pop() || ''; // 保留最后一个可能不完整的行
            
            for (const line of lines) {
                const trimmedLine = line.trim();
                if (!trimmedLine) continue;
                
                // 跳过十六进制chunk大小标识符
                if (/^[0-9a-fA-F]+$/.test(trimmedLine)) {
                    continue;
                }
                
                // 尝试解析JSON数据
                try {
                    const data = JSON.parse(trimmedLine);
                    if (data.type === 'output' && data.content) {
                        appendOutput(data.content, 'info');
                    } else if (data.type === 'error' && data.content) {
                        appendOutput(data.content, 'error');
                    } else if (data.type === 'success' && data.content) {
                        appendOutput(data.content, 'success');
                    } else if (data.type === 'warning' && data.content) {
                        appendOutput(data.content, 'warning');
                    } else if (data.type === 'end' && data.content === 'STREAM_END') {
                        // 流结束标记，跳出循环
                        console.log('收到流结束标记，停止任务监控');
                        stopTaskMonitoring();
                        break;
                    }
                } catch (e) {
                    // 如果不是JSON格式且不是十六进制标识符，直接显示文本
                    if (!/^[0-9a-fA-F]+$/.test(trimmedLine)) {
                        appendOutput(trimmedLine, 'info');
                    }
                }
            }
            
            // 使用setTimeout让出控制权，确保UI能够响应用户操作
            await new Promise(resolve => setTimeout(resolve, 0));
        }
        
        // 执行完成
        appendOutput('✅ 脚本执行流程完成', 'success');
        
    } catch (error) {
        console.error('执行脚本时发生错误:', error);
        
        if (error.name === 'AbortError') {
            appendOutput('🛑 脚本执行已被用户取消', 'warning');
        } else {
            appendOutput(`❌ 执行错误: ${error.message}`, 'error');
            statusDot.className = 'status-dot error';
            statusText.textContent = '错误';
        }
    } finally {
        // 重置UI状态
        resetUIState();
    }
}

// 获取脚本参数
function getScriptParams(scriptType) {
    switch (scriptType) {
        case 'build_folder':
            const buildPath = document.getElementById('build-folder-path').value.trim();
            const buildCount = document.getElementById('build-folder-count').value;
            if (!buildPath) {
                alert('请输入目标目录路径');
                return null;
            }
            if (!buildCount || buildCount < 1) {
                alert('请输入有效的文件夹数量');
                return null;
            }
            return { path: buildPath, count: parseInt(buildCount) };
            
        case 'rename_files':
            const renamePath = document.getElementById('rename-files-path').value.trim();
            if (!renamePath) {
                alert('请输入目标目录路径');
                return null;
            }
            return { path: renamePath };
            
        case 'webp_video':
            const webpPath = document.getElementById('webp-video-path').value.trim();
            const duration = document.getElementById('webp-duration').value;
            const overwrite = document.getElementById('webp-overwrite').value === 'true';
            if (!webpPath) {
                alert('请输入视频目录路径');
                return null;
            }
            return { path: webpPath, duration: parseInt(duration), overwrite: overwrite };
            
        case 'copy_files':
            const sourcePath = document.getElementById('copy-source-path').value.trim();
            const targetPath = document.getElementById('copy-target-path').value.trim();
            if (!sourcePath || !targetPath) {
                alert('请输入素材文件夹和发布文件夹路径');
                return null;
            }
            return { source_path: sourcePath, target_path: targetPath };
            
        case 'unzip':
            const unzipPath = document.getElementById('unzip-path').value.trim();
            const unzipOverwrite = document.getElementById('unzip-overwrite').value === 'true';
            if (!unzipPath) {
                alert('请输入压缩文件目录路径');
                return null;
            }
            return { path: unzipPath, overwrite: unzipOverwrite };
            
        case 'md5_renew':
            const md5Path = document.getElementById('md5-path').value.trim();
            const md5Bytes = document.getElementById('md5-bytes').value;
            if (!md5Path) {
                alert('请输入图片目录路径');
                return null;
            }
            return { path: md5Path, bytes: parseInt(md5Bytes) };
            
        case 'auto_build_copy':
            const autoBasePath = document.getElementById('auto-base-path').value.trim();
            const autoSourcePath = document.getElementById('auto-source-path').value.trim();
            const autoCount = document.getElementById('auto-folder-count').value;
            if (!autoBasePath || !autoSourcePath) {
                alert('请输入基础目录和素材目录路径');
                return null;
            }
            return { base_path: autoBasePath, source_path: autoSourcePath, count: parseInt(autoCount) };
            
        case 'webp_resize':
            const resizePath = document.getElementById('webp-resize-path').value.trim();
            const threshold = document.getElementById('webp-threshold').value;
            const fps = document.getElementById('webp-fps').value;
            if (!resizePath) {
                alert('请输入目录路径');
                return null;
            }
            return { path: resizePath, size_threshold: parseFloat(threshold), fps: parseInt(fps) };
            
        case 'excel_renew':
            const excelPath = document.getElementById('excel-folder-path').value.trim();
            if (!excelPath) {
                alert('请输入Excel文件夹路径');
                return null;
            }
            return { path: excelPath };
            
        case 'test_stop_button':
            // 测试脚本不需要任何参数
            return {};
            
        default:
            alert('未知的脚本类型');
            return null;
    }
}

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 为所有执行按钮添加点击事件
    const executeButtons = document.querySelectorAll('.execute-btn');
    executeButtons.forEach(button => {
        button.addEventListener('click', function() {
            const scriptName = this.getAttribute('data-script');
            const toolItem = this.closest('.tool-item');
            if (scriptName && toolItem) {
                runScript(scriptName, toolItem);
            }
        });
    });
    
    // 工具项悬停效果已移除，现在只通过点击控制展开/收回
    
    // 初始化欢迎消息
    showWelcomeMessage();
    
    // 检查后端服务器状态
    checkServerStatus();
    
    // 添加工具卡片悬停效果
    addCardHoverEffects();
    
    // 自动更新工具数量显示
    updateToolCount();
});

// 显示欢迎消息
function showWelcomeMessage() {
    const outputContent = document.getElementById('output-content');
    outputContent.innerHTML = `
        <div class="welcome-message">
            <i class="fas fa-rocket"></i>
            <h3>欢迎使用小红书工具箱</h3>
            <p>选择左侧的工具开始使用，所有执行结果将在此处显示</p>
            <div class="tips">
                <div class="tip-item">
                    <i class="fas fa-mouse-pointer"></i>
                    <span>悬停工具卡片查看详细选项</span>
                </div>
                <div class="tip-item">
                    <i class="fas fa-play"></i>
                    <span>点击执行按钮开始处理</span>
                </div>
                <div class="tip-item">
                    <i class="fas fa-eye"></i>
                    <span>实时查看处理进度和结果</span>
                </div>
            </div>
        </div>
    `;
}

// 检查服务器状态
async function checkServerStatus() {
    try {
        const response = await fetch('/api/status');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('output-content').innerHTML = 
                `<span class="success">✅ 后端服务器已连接 (${data.message})</span>\n` +
                `<span class="success">📁 工作目录: ${data.working_directory}</span>\n` +
                `<span class="success">🐍 Python版本: ${data.python_version}</span>\n\n` +
                '请选择上方工具开始使用...';
        } else {
            throw new Error('服务器响应异常');
        }
    } catch (error) {
        document.getElementById('output-content').innerHTML = 
            `<span class="error">❌ 无法连接到后端服务器</span>\n` +
            `<span class="error">请确保运行了 server.py 文件</span>\n` +
            `<span class="error">错误信息: ${error.message}</span>`;
    }
}

// 添加输出内容
function appendOutput(text, type = 'info') {
    const outputContent = document.getElementById('output-content');
    const timestamp = new Date().toLocaleTimeString();
    const outputLine = `[${timestamp}] ${text}\n`;
    
    const span = document.createElement('span');
    span.className = type;
    span.textContent = outputLine;
    
    outputContent.appendChild(span);
    outputContent.scrollTop = outputContent.scrollHeight;
}

// 复制输出内容
function copyOutput() {
    const outputContent = document.getElementById('output-content');
    const textContent = outputContent.innerText || outputContent.textContent || '';
    
    if (!textContent.trim()) {
        appendOutput('没有可复制的内容', 'warning');
        return;
    }
    
    // 使用现代的 Clipboard API
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(textContent).then(() => {
            appendOutput('✅ 输出内容已复制到剪贴板', 'success');
        }).catch(err => {
            console.error('复制失败:', err);
            fallbackCopyTextToClipboard(textContent);
        });
    } else {
        // 降级方案
        fallbackCopyTextToClipboard(textContent);
    }
}

// 降级复制方案
function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            appendOutput('✅ 输出内容已复制到剪贴板', 'success');
        } else {
            appendOutput('❌ 复制失败，请手动选择并复制', 'error');
        }
    } catch (err) {
        console.error('降级复制方案失败:', err);
        appendOutput('❌ 复制失败，请手动选择并复制', 'error');
    }
    
    document.body.removeChild(textArea);
}

// 清空输出
function clearOutput() {
    const outputContent = document.getElementById('output-content');
    outputContent.innerHTML = '';
    
    // 重置状态
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-indicator span');
    statusDot.className = 'status-dot';
    statusText.textContent = '就绪';
}

// 全屏切换
function toggleFullscreen() {
    const outputPanel = document.querySelector('.output-panel');
    outputPanel.classList.toggle('fullscreen');
    
    const icon = document.querySelector('[onclick="toggleFullscreen()"] i');
    if (outputPanel.classList.contains('fullscreen')) {
        icon.className = 'fas fa-compress';
    } else {
        icon.className = 'fas fa-expand';
    }
}

// 添加工具卡片悬停效果（仅视觉效果，不影响展开状态）
function addCardHoverEffects() {
    const toolItems = document.querySelectorAll('.tool-item');
    
    toolItems.forEach(item => {
        item.addEventListener('mouseenter', function() {
            // 移除transform效果，避免影响展开状态
            this.style.boxShadow = '0 8px 25px rgba(0,0,0,0.15)';
        });
        
        item.addEventListener('mouseleave', function() {
            this.style.boxShadow = '0 4px 15px rgba(0,0,0,0.1)';
        });
    });
}

// 自动更新工具数量显示
function updateToolCount() {
    const toolItems = document.querySelectorAll('.tool-item');
    const toolCount = toolItems.length;
    const toolCountElement = document.getElementById('tool-count');
    
    if (toolCountElement) {
        toolCountElement.textContent = `${toolCount}个工具`;
    }
    
    console.log(`检测到 ${toolCount} 个工具`);
}

// 添加键盘快捷键支持
document.addEventListener('keydown', function(event) {
    // Ctrl + L 清除输出
    if (event.ctrlKey && event.key === 'l') {
        event.preventDefault();
        clearOutput();
    }
    
    // F11 切换全屏
    if (event.key === 'F11') {
        event.preventDefault();
        toggleFullscreen();
    }
    
    // ESC 退出全屏
    if (event.key === 'Escape') {
        const outputSection = document.querySelector('.output-section');
        if (outputSection.classList.contains('fullscreen')) {
            toggleFullscreen();
        }
    }
    
    // Ctrl + C 终止脚本
    if (event.ctrlKey && event.key === 'c') {
        event.preventDefault();
        stopScript();
    }
});

// 工具项点击展开收回功能
function initToolItemToggle() {
    const toolItems = document.querySelectorAll('.tool-item');
    
    toolItems.forEach((toolItem) => {
        const toolHeader = toolItem.querySelector('.tool-header');
        
        if (toolHeader) {
            // 移除可能存在的旧事件监听器
            toolHeader.removeEventListener('click', handleToolHeaderClick);
            
            // 添加新的事件监听器
            toolHeader.addEventListener('click', function(e) {
                handleToolHeaderClick(e, toolItem);
            });
        }
    });
}

// 处理工具头部点击事件的函数
function handleToolHeaderClick(e, toolItem) {
    // 防止事件冒泡
    e.stopPropagation();
    
    // 防止点击执行按钮时触发展开收回
    if (e.target.closest('.execute-btn')) {
        return;
    }
    
    // 切换当前工具项的展开状态
    const isExpanded = toolItem.classList.contains('expanded');
    toolItem.classList.toggle('expanded');
    
    // 更新展开指示器的状态
    const expandIndicator = toolItem.querySelector('.expand-indicator i');
    if (expandIndicator) {
        if (isExpanded) {
            expandIndicator.style.transform = 'rotate(0deg)';
        } else {
            expandIndicator.style.transform = 'rotate(180deg)';
        }
    }
}

// 页面加载完成后初始化工具项点击功能和事件监听器
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        initToolItemToggle();
        initEventListeners();
    });
} else {
    initToolItemToggle();
    initEventListeners();
}

// 初始化事件监听器
function initEventListeners() {
    // 绑定全局终止按钮点击事件
    const stopButton = document.getElementById('stop-btn');
    if (stopButton) {
        stopButton.addEventListener('click', stopScript);
    }
    
    // 绑定所有内联终止按钮点击事件
    const inlineStopButtons = document.querySelectorAll('.stop-btn-inline');
    inlineStopButtons.forEach(button => {
        button.addEventListener('click', stopScript);
    });
    
    // 绑定服务状态按钮点击事件
    const serverStatusButton = document.getElementById('server-status-btn');
    if (serverStatusButton) {
        serverStatusButton.addEventListener('click', openServerStatusModal);
    }
}

// ===== 服务状态弹窗相关功能 =====

/**
 * 打开服务状态弹窗
 * 目的：显示服务器状态对话框并加载最新状态信息
 */
function openServerStatusModal() {
    const modal = document.getElementById('server-status-modal');
    if (modal) {
        modal.style.display = 'flex';
        // 添加短暂延迟以确保CSS过渡效果正常
        setTimeout(() => {
            modal.classList.add('show');
        }, 10);
        
        // 立即加载服务器状态
        refreshServerStatus();
    }
}

/**
 * 关闭服务状态弹窗
 * 目的：隐藏服务器状态对话框
 */
function closeServerStatusModal() {
    const modal = document.getElementById('server-status-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
    }
}

/**
 * 刷新服务器状态
 * 目的：获取并更新服务器的最新状态信息
 */
async function refreshServerStatus() {
    const statusElements = {
        runningStatus: document.getElementById('server-running-status'),
        workDir: document.getElementById('server-work-dir'),
        pythonVersion: document.getElementById('server-python-version'),
        toolCount: document.getElementById('server-tool-count'),
        logs: document.getElementById('server-logs')
    };
    
    // 显示加载状态
    if (statusElements.runningStatus) {
        statusElements.runningStatus.textContent = '检查中...';
        statusElements.runningStatus.className = 'status-value';
    }
    
    try {
        const response = await fetch('/api/status');
        if (response.ok) {
            const data = await response.json();
            
            // 更新状态信息
            if (statusElements.runningStatus) {
                statusElements.runningStatus.textContent = '正常运行';
                statusElements.runningStatus.className = 'status-value running';
            }
            
            if (statusElements.workDir) {
                statusElements.workDir.textContent = data.working_directory || '-';
            }
            
            if (statusElements.pythonVersion) {
                statusElements.pythonVersion.textContent = data.python_version || '-';
            }
            
            if (statusElements.toolCount) {
                const toolCount = data.available_scripts ? data.available_scripts.length : 0;
                statusElements.toolCount.textContent = `${toolCount} 个工具`;
            }
            
            // 更新日志
            updateServerLogs([
                { type: 'success', message: '✅ 服务器状态检查完成' },
                { type: 'info', message: `📊 服务状态: ${data.message}` },
                { type: 'info', message: `📁 工作目录: ${data.working_directory}` },
                { type: 'info', message: `🐍 Python版本: ${data.python_version}` },
                { type: 'info', message: `🛠️ 可用工具: ${data.available_scripts ? data.available_scripts.length : 0} 个` }
            ]);
            
        } else {
            throw new Error(`服务器响应错误: ${response.status}`);
        }
    } catch (error) {
        console.error('检查服务器状态失败:', error);
        
        // 更新错误状态
        if (statusElements.runningStatus) {
            statusElements.runningStatus.textContent = '连接失败';
            statusElements.runningStatus.className = 'status-value error';
        }
        
        // 更新错误日志
        updateServerLogs([
            { type: 'error', message: '❌ 服务器状态检查失败' },
            { type: 'error', message: `错误信息: ${error.message}` },
            { type: 'warning', message: '⚠️ 请检查服务器是否正常运行' }
        ]);
    }
}

/**
 * 更新服务器日志显示
 * 目的：在弹窗中显示服务器相关的日志信息
 */
function updateServerLogs(logs) {
    const logsContainer = document.getElementById('server-logs');
    if (!logsContainer) return;
    
    logsContainer.innerHTML = '';
    
    logs.forEach(log => {
        const logItem = document.createElement('div');
        logItem.className = `log-item ${log.type}`;
        logItem.textContent = log.message;
        logsContainer.appendChild(logItem);
    });
    
    // 滚动到底部
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

/**
 * 重启服务器
 * 目的：尝试重启服务器（需要服务器端支持）
 */
async function restartServer() {
    if (!confirm('确定要重启服务器吗？这将中断当前所有操作。')) {
        return;
    }
    
    const logs = [
        { type: 'warning', message: '⚠️ 正在尝试重启服务器...' }
    ];
    updateServerLogs(logs);
    
    try {
        // 尝试调用重启API（如果服务器支持）
        const response = await fetch('/api/restart-server', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            logs.push({ type: 'success', message: '✅ 重启命令已发送' });
            logs.push({ type: 'info', message: 'ℹ️ 服务器正在重启，请稍候...' });
        } else {
            throw new Error('重启API不可用');
        }
    } catch (error) {
        // 如果API不存在，提供手动重启指导
        logs.push({ type: 'error', message: '❌ 自动重启功能不可用' });
        logs.push({ type: 'info', message: '💡 请手动重启服务器:' });
        logs.push({ type: 'info', message: '1. 在服务器控制台按 Ctrl+C' });
        logs.push({ type: 'info', message: '2. 重新运行 python environment/server.py' });
        logs.push({ type: 'info', message: '3. 或运行 Restart_server.bat' });
    }
    
    updateServerLogs(logs);
}

/**
 * 停止服务器
 * 目的：尝试停止服务器（需要服务器端支持）
 */
async function stopServer() {
    if (!confirm('确定要停止服务器吗？这将关闭Web界面。')) {
        return;
    }
    
    const logs = [
        { type: 'warning', message: '⚠️ 正在尝试停止服务器...' }
    ];
    updateServerLogs(logs);
    
    try {
        // 尝试调用停止API（如果服务器支持）
        const response = await fetch('/api/shutdown-server', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            logs.push({ type: 'success', message: '✅ 停止命令已发送' });
            logs.push({ type: 'warning', message: '⚠️ 服务器即将关闭...' });
        } else {
            throw new Error('停止API不可用');
        }
    } catch (error) {
        // 如果API不存在，提供手动停止指导
        logs.push({ type: 'error', message: '❌ 自动停止功能不可用' });
        logs.push({ type: 'info', message: '💡 请手动停止服务器:' });
        logs.push({ type: 'info', message: '1. 在服务器控制台按 Ctrl+C' });
        logs.push({ type: 'info', message: '2. 或关闭控制台窗口' });
    }
    
    updateServerLogs(logs);
}

// 点击弹窗外部关闭弹窗
document.addEventListener('click', function(event) {
    const modal = document.getElementById('server-status-modal');
    if (modal && event.target === modal) {
        closeServerStatusModal();
    }
});

// 键盘ESC键关闭弹窗
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('server-status-modal');
        if (modal && modal.style.display !== 'none') {
            closeServerStatusModal();
        }
    }
});

// ===== 任务监控和状态检查功能 =====

/**
 * 定期检查活动任务状态
 * 目的：提供实时的任务状态监控，确保UI状态同步
 */
let taskMonitorInterval = null;

function startTaskMonitoring() {
    if (taskMonitorInterval) {
        clearInterval(taskMonitorInterval);
    }
    
    console.log('启动任务监控');
    taskMonitorInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/tasks');
            if (response.ok) {
                const data = await response.json();
                updateTaskStatus(data);
            }
        } catch (error) {
            console.error('检查任务状态失败:', error);
        }
    }, 5000); // 改为每5秒检查一次，减少频率
}

function stopTaskMonitoring() {
    if (taskMonitorInterval) {
        console.log('停止任务监控');
        clearInterval(taskMonitorInterval);
        taskMonitorInterval = null;
    }
}

/**
 * 更新任务状态显示
 * 目的：根据服务器返回的任务状态更新UI
 */
function updateTaskStatus(taskData) {
    const { active_tasks, process_count, total_tasks } = taskData;
    
    // 更新状态指示器
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.querySelector('.status-indicator span');
    const stopButton = document.getElementById('stop-btn');
    
    if (active_tasks.length > 0) {
        // 有活动任务
        if (!isScriptRunning) {
            // 前端状态不同步，更新前端状态
            isScriptRunning = true;
            if (statusDot) statusDot.className = 'status-dot running';
            if (statusText) statusText.textContent = `运行中 (${active_tasks.length}个任务)`;
            if (stopButton) stopButton.style.display = 'flex';
        }
    } else {
        // 没有活动任务
        if (isScriptRunning) {
            // 前端状态不同步，重置前端状态
            resetUIState();
        }
        // 没有活动任务时停止监控，减少不必要的请求
        if (taskMonitorInterval) {
            console.log('没有活动任务，停止监控');
            stopTaskMonitoring();
        }
    }
    
    // 更新头部统计信息
    const toolCountElement = document.getElementById('tool-count');
    if (toolCountElement && active_tasks.length > 0) {
        toolCountElement.textContent = `${document.querySelectorAll('.tool-item').length}个工具 (${active_tasks.length}个运行中)`;
    } else if (toolCountElement) {
        toolCountElement.textContent = `${document.querySelectorAll('.tool-item').length}个工具`;
    }
}

/**
 * 增强的停止脚本函数，支持强制停止
 * 目的：提供更可靠的停止机制
 */
async function forceStopAllScripts() {
    try {
        appendOutput('🛑 正在强制停止所有脚本...', 'warning');
        
        // 先取消当前的fetch请求
        if (abortController) {
            abortController.abort();
        }
        
        // 调用服务器停止API
        const response = await fetch('/api/stop-script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ force: true })
        });
        
        if (response.ok) {
            const result = await response.json();
            appendOutput(`✅ ${result.message}`, 'success');
        }
        
        // 重置所有状态
        resetUIState();
        
        // 等待一秒后再次检查状态
        setTimeout(async () => {
            try {
                const taskResponse = await fetch('/api/tasks');
                if (taskResponse.ok) {
                    const taskData = await taskResponse.json();
                    if (taskData.active_tasks.length > 0) {
                        appendOutput('⚠️ 仍有任务在运行，可能需要手动终止', 'warning');
                    } else {
                        appendOutput('✅ 所有任务已成功停止', 'success');
                    }
                }
            } catch (error) {
                console.error('检查停止结果失败:', error);
            }
        }, 1000);
        
    } catch (error) {
        console.error('强制停止失败:', error);
        appendOutput(`❌ 强制停止失败: ${error.message}`, 'error');
    }
}

// 页面加载时启动任务监控
document.addEventListener('DOMContentLoaded', function() {
    // 不再自动启动监控，只在有任务执行时才启动
    console.log('🚀 小红书工具箱已加载');
    console.log('💡 任务监控将在有脚本执行时自动启动');
});

// 页面卸载时停止监控
window.addEventListener('beforeunload', function() {
    stopTaskMonitoring();
});

// 添加键盘快捷键 Ctrl+Shift+S 用于强制停止所有脚本
document.addEventListener('keydown', function(event) {
    if (event.ctrlKey && event.shiftKey && event.key === 'S') {
        event.preventDefault();
        forceStopAllScripts();
    }
});

console.log('🚀 小红书工具箱已加载 - 支持异步执行和多线程处理');
console.log('💡 快捷键提示:');
console.log('   - Ctrl+C: 终止当前脚本');
console.log('   - Ctrl+Shift+S: 强制停止所有脚本');
console.log('   - F11: 切换全屏模式');
console.log('   - ESC: 关闭弹窗');