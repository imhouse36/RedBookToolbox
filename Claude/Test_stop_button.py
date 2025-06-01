#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
终止按钮测试脚本

功能说明：
- 创建一个长时间运行的测试脚本，用于测试Web界面的终止按钮功能
- 脚本会运行30步，每步间隔2秒，总共约60秒
- 在执行过程中可以通过Web界面的终止按钮来中断执行
- 支持优雅的中断处理，显示详细的执行进度

使用方法：
1. 通过Web界面选择此工具
2. 点击"开始执行"按钮
3. 在执行过程中可以点击"终止执行"按钮来测试终止功能

注意事项：
- 此脚本专门用于测试终止按钮功能
- 脚本会输出详细的执行进度信息
- 支持键盘中断(Ctrl+C)和进程终止信号
"""

import time
import sys
import signal
import os
from datetime import datetime

def signal_handler(signum, frame):
    """信号处理函数，用于优雅地处理终止信号"""
    print(f"\n🛑 收到终止信号 {signum}，正在安全退出...")
    print(f"⏰ 退出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("✅ 测试脚本已被用户成功终止")
    print("\n💡 终止按钮功能测试: 通过 ✓")
    sys.exit(0)

def main():
    """主函数：执行长时间运行的测试任务"""
    # 注册信号处理器
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    print("="*60)
    print("🧪 终止按钮功能测试脚本")
    print("="*60)
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🆔 进程ID: {os.getpid()}")
    print("\n📋 测试说明:")
    print("- 脚本将运行30步，每步间隔2秒")
    print("- 总预计运行时间: 约60秒")
    print("- 可以随时点击'终止执行'按钮来测试终止功能")
    print("- 脚本支持优雅的中断处理")
    print("\n🚀 开始执行测试任务...\n")
    
    try:
        total_steps = 30
        
        for i in range(total_steps):
            current_step = i + 1
            progress_percent = (current_step / total_steps) * 100
            
            # 创建进度条
            bar_length = 30
            filled_length = int(bar_length * current_step // total_steps)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            print(f"⏳ 步骤 {current_step:2d}/{total_steps} [{bar}] {progress_percent:5.1f}% - {datetime.now().strftime('%H:%M:%S')}")
            
            # 每5步显示一次详细信息
            if current_step % 5 == 0:
                elapsed_time = current_step * 2
                remaining_time = (total_steps - current_step) * 2
                print(f"   📊 已用时: {elapsed_time}秒, 剩余时间: {remaining_time}秒")
            
            # 模拟工作负载
            time.sleep(2)
            
            # 强制刷新输出缓冲区
            sys.stdout.flush()
        
        # 测试完成
        print("\n" + "="*60)
        print("✅ 测试脚本执行完成!")
        print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️ 总执行时间: {total_steps * 2}秒")
        print("\n🎉 如果您看到这条消息，说明脚本自然结束")
        print("💡 如果脚本被终止，您应该会看到终止信号的处理消息")
        print("\n📝 测试结果: 脚本完整运行，未被终止")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n⚠️  收到键盘中断信号 (Ctrl+C)")
        print(f"⏰ 中断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("✅ 测试脚本已被手动中断")
        print("\n💡 终止按钮功能测试: 通过 ✓")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 脚本执行过程中发生错误: {str(e)}")
        print(f"⏰ 错误时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        sys.exit(1)

if __name__ == "__main__":
    main()