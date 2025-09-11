#!/usr/bin/env python3

"""
测试Playwright图表导出功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, '.')

# 设置环境变量
os.environ['FLASK_APP'] = 'app.py'

from app import create_app
from models import LLM
from utils import generate_leaderboard_data
from config import RATERS
import time
import logging

def test_playwright_export():
    """测试Playwright图表导出功能"""
    app = create_app()
    
    with app.app_context():
        # 获取所有非评分模型
        rater_names = [rater for raters in RATERS.values() for rater in raters]
        models = LLM.query.filter(LLM.name.notin_(rater_names)).all()
        
        print(f"找到 {len(models)} 个模型需要导出图表")
        for model in models:
            print(f"- {model.name}")
        
        if not models:
            print("没有找到可导出的模型")
            return
        
        # 生成榜单数据
        print("\n生成榜单数据...")
        leaderboard_result = generate_leaderboard_data()
        leaderboard_data = leaderboard_result['leaderboard']
        l1_dims = leaderboard_result['l1_dimensions']
        
        print(f"生成的榜单数据包含 {len(leaderboard_data)} 个模型")
        print(f"包含 {len(l1_dims)} 个一级维度")
        
        # 创建temp/imgs文件夹
        imgs_dir = Path('./temp/imgs_playwright')
        imgs_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = int(time.time())
        
        # 直接调用Playwright导出函数
        from routes.index import _export_charts_with_playwright
        
        logger = logging.getLogger('test_playwright_export')
        
        print(f"\n开始使用Playwright导出图表，时间戳: {timestamp}")
        
        try:
            exported_count = _export_charts_with_playwright(
                models, leaderboard_data, l1_dims, imgs_dir, timestamp, logger
            )
            print(f"\n成功导出 {exported_count} 个图表")
            
            # 检查生成的文件
            print("\n生成的文件:")
            for file_path in imgs_dir.glob("*.png"):
                file_size = file_path.stat().st_size
                print(f"  {file_path.name} ({file_size} bytes)")
                
        except Exception as e:
            print(f"导出过程中出现错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_playwright_export()