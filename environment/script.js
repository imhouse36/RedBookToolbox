// 全局变量
let currentProcess = null;

// 终止脚本函数 - 全局作用域
async function stopScript() {
    try {
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
        
        // 显示终止结果
        const outputContent = document.getElementById('output-content');
        if (result.status === 'success') {
            if (typeof appendOutput === 'function') {
                appendOutput('=== 脚本已被用户终止 ===', 'warning');
            } else {
                outputContent.innerHTML += '<div class="output-line warning">🟡 === 脚本已被用户终止 ===</div>';
            }
        } else if (result.status === 'info') {
            if (typeof appendOutput === 'function') {
                appendOutput('当前没有正在运行的脚本', 'info');
            } else {
                outputContent.innerHTML += '<div class="output-line info">ℹ️ 当前没有正在运行的脚本</div>';
            }
        }
        
        // 更新UI状态
        const statusDot = document.querySelector('.status-dot');
        const statusText = document.querySelector('.status-indicator span');
        const stopButton = document.getElementById('stop-btn');
        const loadingOverlay = document.getElementById('loading-overlay');
        
        statusDot.className = 'status-dot';
        statusText.textContent = '就绪';
        stopButton.style.display = 'none';
        loadingOverlay.classList.remove('show');
        
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
        
    } catch (error) {
        console.error('终止脚本失败:', error);
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
    }
}

// 运行脚本函数
async function runScript(scriptName, toolItem) {
    const formData = new FormData();
    formData.append('script', scriptName);
    
    // 获取工具项中的所有输入参数
    const inputs = toolItem.querySelectorAll('input, select');
    inputs.forEach(input => {
        if (input.value.trim()) {
            formData.append(input.name, input.value.trim());
        }
    });
    
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
        const response = await fetch('/api/run-script', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        
        // 一旦开始接收数据流，立即隐藏loading overlay以显示实时输出
        loadingOverlay.classList.remove('show');
        
        while (true) {
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
                    }
                } catch (e) {
                    // 如果不是JSON格式且不是十六进制标识符，直接显示文本
                    if (!/^[0-9a-fA-F]+$/.test(trimmedLine)) {
                        appendOutput(trimmedLine, 'info');
                    }
                }
            }
        }
        
        // 执行完成
        statusDot.className = 'status-dot';
        statusText.textContent = '就绪';
        stopButton.style.display = 'none'; // 隐藏全局终止按钮
        
        // 隐藏当前工具的内联终止按钮
        const inlineStopButton = toolItem.querySelector('.stop-btn-inline');
        if (inlineStopButton) {
            inlineStopButton.style.display = 'none';
        }
        
    } catch (error) {
        console.error('Error:', error);
        appendOutput(`错误: ${error.message}`, 'error');
        statusDot.className = 'status-dot error';
        statusText.textContent = '错误';
    } finally {
        // loading overlay已在开始接收数据时隐藏，这里不需要重复操作
        runButton.disabled = false;
        runButton.innerHTML = '<i class="fas fa-play"></i> 开始执行';
        stopButton.style.display = 'none'; // 确保隐藏全局终止按钮
        
        // 确保隐藏当前工具的内联终止按钮
        const inlineStopButton = toolItem.querySelector('.stop-btn-inline');
        if (inlineStopButton) {
            inlineStopButton.style.display = 'none';
        }
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
}