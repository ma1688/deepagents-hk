#!/usr/bin/env python
"""
启动 Chainlit HKEX Agent 服务器的脚本。

Usage:
    python run.py [--port PORT] [--host HOST]
    
或者直接使用 chainlit：
    chainlit run app.py -w
"""

import os
import sys
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="启动 HKEX Agent Chainlit 服务器")
    parser.add_argument("--port", "-p", type=int, default=8000, help="服务器端口 (默认: 8000)")
    parser.add_argument("--host", "-H", default="0.0.0.0", help="服务器地址 (默认: 0.0.0.0)")
    parser.add_argument("--watch", "-w", action="store_true", help="启用热重载")
    parser.add_argument("--headless", action="store_true", help="无头模式（不自动打开浏览器）")
    
    args = parser.parse_args()
    
    # 切换到 chainlit 目录
    chainlit_dir = Path(__file__).parent
    os.chdir(chainlit_dir)
    
    # 设置项目根目录环境变量
    project_root = chainlit_dir.parent
    os.environ["HKEX_PROJECT_ROOT"] = str(project_root)
    
    # 构建 chainlit 命令
    cmd = ["chainlit", "run", "app.py"]
    cmd.extend(["--port", str(args.port)])
    cmd.extend(["--host", args.host])
    
    if args.watch:
        cmd.append("-w")
    
    if args.headless:
        cmd.append("--headless")
    
    # 执行 chainlit
    os.execvp("chainlit", cmd)


if __name__ == "__main__":
    main()

