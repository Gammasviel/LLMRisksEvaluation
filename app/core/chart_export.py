# chart_export.py

import logging
from playwright.sync_api import sync_playwright
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

logger = logging.getLogger('chart_export')


def export_charts_with_playwright(models, leaderboard_data, l1_dims, imgs_dir, timestamp, export_timestamp=True):
    """使用Playwright导出真实的图表"""
    
    exported_count = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-proxy-server',  # 禁用代理服务器
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
        )
        page = browser.new_page()
        page.set_viewport_size({"width": 1200, "height": 800})
        
        # 设置基础URL
        base_url = "http://localhost:5000"  # 需要根据实际情况调整
        
        try:
            # 1. 导出公共榜单的综合图表
            leaderboard_url = f"{base_url}/"  # 使用根路径访问公共榜单
            logger.info(f"Accessing public leaderboard at: {leaderboard_url}")
            page.goto(leaderboard_url)
            
            # 等待页面完全加载，特别是ECharts图表
            page.wait_for_timeout(5000)  # 增加等待时间到5秒
            
            # 等待所有图表元素出现
            try:
                page.wait_for_selector('#overall-bar-chart', timeout=10000)
                logger.info("Overall bar chart element found")
            except Exception as e:
                logger.warning(f"Overall bar chart element not found: {e}")
            
            # 导出综合图表
            if export_timestamp:
                chart_selectors = [
                    ('#overall-bar-chart', f'overall_bar_chart_{timestamp}.png'),
                    ('#quadrant-chart', f'quadrant_chart_{timestamp}.png'),
                    ('#dimension-bar-chart', f'dimension_bar_chart_{timestamp}.png'),
                    ('#question-type-bar-chart', f'question_type_bar_chart_{timestamp}.png')
                ]
            else:
                chart_selectors = [
                    ('#overall-bar-chart', f'overall_bar_chart.png'),
                    ('#quadrant-chart', f'quadrant_chart.png'),
                    ('#dimension-bar-chart', f'dimension_bar_chart.png'),
                    ('#question-type-bar-chart', f'question_type_bar_chart.png')
                ]
            
            for selector, filename in chart_selectors:
                try:
                    element = page.query_selector(selector)
                    if element:
                        # 检查元素是否实际包含内容
                        bounding_box = element.bounding_box()
                        if bounding_box and bounding_box['width'] > 0 and bounding_box['height'] > 0:
                            screenshot_path = imgs_dir / filename
                            element.screenshot(path=str(screenshot_path))
                            exported_count += 1
                            logger.info(f"Successfully exported chart: {filename}")
                        else:
                            logger.warning(f"Chart element {selector} has no content")
                    else:
                        logger.warning(f"Chart element not found: {selector}")
                except Exception as e:
                    logger.warning(f"Failed to export chart {filename}: {e}")
            
            # 2. 导出每个模型的详细图表
            for model in models:
                model_name = model.name
                
                # 访问模型详情页面
                model_detail_url = f"{base_url}/model/detail/{model_name}"
                page.goto(model_detail_url)
                page.wait_for_timeout(3000)  # 等待图表加载
                
                # 导出模型详情图表
                if export_timestamp:
                    model_chart_selectors = [
                        ('#response-efficiency-chart', f'{model_name}_response_rate_{timestamp}.png'),
                        ('#pie-chart', f'{model_name}_avg_scores_{timestamp}.png')
                    ]
                else:
                    model_chart_selectors = [
                        ('#response-efficiency-chart', f'{model_name}_response_rate.png'),
                        ('#pie-chart', f'{model_name}_avg_scores.png')
                    ]
                
                for selector, filename in model_chart_selectors:
                    try:
                        element = page.query_selector(selector)
                        if element:
                            screenshot_path = imgs_dir / filename
                            element.screenshot(path=str(screenshot_path))
                            exported_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to export chart {filename}: {e}")
                
                # 导出偏见歧视分析表格（如果存在）
                bias_table = page.query_selector('table.tech-table')
                if bias_table:
                    try:
                        
                        if export_timestamp:
                            screenshot_path = imgs_dir / f'{model_name}_bias_analysis_{timestamp}.png'
                        else:
                            screenshot_path = imgs_dir / f'{model_name}_bias_analysis.png'
                            
                        bias_table.screenshot(path=str(screenshot_path))
                        exported_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to export bias analysis table for {model_name}: {e}")
                        
        except Exception as e:
            logger.error(f"Error during Playwright chart export: {e}")
        finally:
            browser.close()
    
    return exported_count


def export_charts_with_matplotlib(models, leaderboard_data, l1_dims, imgs_dir, timestamp, export_timestamp=True):
    """使用matplotlib生成真实的图表"""
    
    exported_count = 0
    plt.style.use('default')
    
    try:
        # 提取榜单数据 - 修复数据结构访问
        model_data = leaderboard_data  # leaderboard_data已经是模型数据列表
        
        # 1. 导出综合排名条形图
        model_names = [data['name'] for data in model_data]
        avg_scores = [data['avg_score'] for data in model_data]
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(model_names, avg_scores)
        plt.xlabel('平均分数')
        plt.title('模型综合排名')
        plt.gca().invert_yaxis()
        
        # 添加数值标签
        for i, bar in enumerate(bars):
            width = bar.get_width()
            plt.text(width + 0.01, bar.get_y() + bar.get_height()/2, 
                    f'{avg_scores[i]:.2f}', ha='left', va='center')
        
        plt.tight_layout()
        
        if export_timestamp:
            plt.savefig(imgs_dir / f'overall_bar_chart_{timestamp}.png', dpi=300, bbox_inches='tight')
        else:
            plt.savefig(imgs_dir / f'overall_bar_chart.png', dpi=300, bbox_inches='tight')
        
        plt.close()
        exported_count += 1
        
        # 2. 导出象限图
        subj_scores = [data['avg_subj_score'] for data in model_data]
        obj_scores = [data['avg_obj_score'] for data in model_data]
        
        plt.figure(figsize=(10, 8))
        plt.scatter(subj_scores, obj_scores, s=100, alpha=0.7)
        
        # 添加模型名称标签
        for i, name in enumerate(model_names):
            plt.annotate(name, (subj_scores[i], obj_scores[i]), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        plt.xlabel('主观题平均分')
        plt.ylabel('客观题平均分')
        plt.title('模型表现象限图')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if export_timestamp:
            plt.savefig(imgs_dir / f'quadrant_chart_{timestamp}.png', dpi=300, bbox_inches='tight')
        else:
            plt.savefig(imgs_dir / f'quadrant_chart.png', dpi=300, bbox_inches='tight')
            
        plt.close()
        exported_count += 1
        
        # 3. 导出维度条形图
        if l1_dims:
            fig, ax = plt.subplots(figsize=(14, 8))
            
            dim_names = [dim['name'] for dim in l1_dims]
            x_pos = np.arange(len(dim_names))
            bar_width = 0.8 / len(model_data)
            
            for i, model in enumerate(model_data):
                dim_scores = [model['dim_scores'].get(dim['id'], {}).get('avg', 0) 
                             for dim in l1_dims]
                ax.bar(x_pos + i * bar_width, dim_scores, bar_width, 
                      label=model['name'], alpha=0.8)
            
            ax.set_xlabel('评估维度')
            ax.set_ylabel('平均分数')
            ax.set_title('各维度评分对比')
            ax.set_xticks(x_pos + bar_width * (len(model_data) - 1) / 2)
            ax.set_xticklabels(dim_names, rotation=45, ha='right')
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            if export_timestamp:
                plt.savefig(imgs_dir / f'dimension_bar_chart_{timestamp}.png', dpi=300, bbox_inches='tight')
            else:
                plt.savefig(imgs_dir / f'dimension_bar_chart.png', dpi=300, bbox_inches='tight')
                
            plt.close()
            exported_count += 1
        
        # 4. 导出题型分布图
        plt.figure(figsize=(10, 6))
        
        # 计算各模型在主观题和客观题上的平均表现
        subj_data = []
        obj_data = []
        model_labels = []
        
        for model in model_data:
            if model['avg_subj_score'] > 0:
                subj_data.append(model['avg_subj_score'])
                model_labels.append(model['name'])
            if model['avg_obj_score'] > 0:
                obj_data.append(model['avg_obj_score'])
        
        x_pos = np.arange(len(model_labels))
        width = 0.35
        
        plt.bar(x_pos - width/2, subj_data, width, label='主观题', alpha=0.8)
        plt.bar(x_pos + width/2, obj_data, width, label='客观题', alpha=0.8)
        
        plt.xlabel('模型')
        plt.ylabel('平均分数')
        plt.title('主观题vs客观题表现对比')
        plt.xticks(x_pos, model_labels, rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        if export_timestamp:
            plt.savefig(imgs_dir / f'question_type_bar_chart_{timestamp}.png', dpi=300, bbox_inches='tight')
        else:
            plt.savefig(imgs_dir / f'question_type_bar_chart.png', dpi=300, bbox_inches='tight')
            
        plt.close()
        exported_count += 1
        
        # 5. 为每个模型生成详细图表
        for model in models:
            model_name = model.name
            model_detail_data = next((m for m in model_data if m['name'] == model_name), None)
            
            if not model_detail_data:
                continue
                
            # 响应率图表
            plt.figure(figsize=(8, 6))
            responsive_rate = model_detail_data['response_rate']
            non_responsive_rate = 100 - responsive_rate
            
            sizes = [responsive_rate, non_responsive_rate]
            labels = ['有效响应', '无效响应']
            colors = ['#2ecc71', '#e74c3c']
            
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.title(f'{model_name} - 响应有效性')
            plt.axis('equal')
            plt.tight_layout()
            
            if export_timestamp:
                plt.savefig(imgs_dir / f'{model_name}_response_rate_{timestamp}.png', dpi=300, bbox_inches='tight')
            else:
                plt.savefig(imgs_dir / f'{model_name}_response_rate.png', dpi=300, bbox_inches='tight')
                
            plt.close()
            exported_count += 1
            
            # 各维度得分饼图
            if model_detail_data['dim_scores']:
                plt.figure(figsize=(8, 8))
                
                dim_scores = []
                dim_labels = []
                
                for dim in l1_dims:
                    dim_score_data = model_detail_data['dim_scores'].get(dim['id'], {})
                    if dim_score_data and dim_score_data.get('avg', 0) > 0:
                        dim_scores.append(dim_score_data['avg'])
                        dim_labels.append(dim['name'])
                
                if dim_scores:
                    plt.pie(dim_scores, labels=dim_labels, autopct='%1.2f', startangle=90)
                    plt.title(f'{model_name} - 各维度平均得分')
                    plt.axis('equal')
                    plt.tight_layout()
                    
                    if export_timestamp:
                        plt.savefig(imgs_dir / f'{model_name}_avg_scores_{timestamp}.png', dpi=300, bbox_inches='tight')
                    else:
                        plt.savefig(imgs_dir / f'{model_name}_avg_scores_{timestamp}.png', dpi=300, bbox_inches='tight')
                        
                    plt.close()
                    exported_count += 1
                    
    except Exception as e:
        logger.error(f"Error generating matplotlib charts: {e}", exc_info=True)
    
    return exported_count


def export_charts_placeholder(models, imgs_dir, timestamp, export_timestamp=True):
    """创建占位符文件"""
    exported_count = 0
    
    # 为每个模型创建对应的图表文件
    for model in models:
        model_name = model.name
        
        if export_timestamp:
            charts = [
                f'{model_name}_response_rate_{timestamp}.png',
                f'{model_name}_avg_scores_{timestamp}.png',
                f'{model_name}_bias_analysis_{timestamp}.png'
            ]
        else:
            charts = [
                f'{model_name}_response_rate.png',
                f'{model_name}_avg_scores.png',
                f'{model_name}_bias_analysis.png'
            ]
        
        for chart_filename in charts:
            chart_path = imgs_dir / chart_filename
            # 创建占位符文件（实际实现中这里会生成真实的图表）
            chart_path.write_text(f'Placeholder for {chart_filename}')
            exported_count += 1
    
    # 导出综合图表
    if export_timestamp:
        overall_charts = [
            f'overall_bar_chart_{timestamp}.png',
            f'quadrant_chart_{timestamp}.png', 
            f'dimension_bar_chart_{timestamp}.png',
            f'question_type_bar_chart_{timestamp}.png'
        ]
    else:
        overall_charts = [
            f'overall_bar_chart.png',
            f'quadrant_chart.png', 
            f'dimension_bar_chart.png',
            f'question_type_bar_chart.png'
        ]
    
    for chart_filename in overall_charts:
        chart_path = imgs_dir / chart_filename
        chart_path.write_text(f'Placeholder for {chart_filename}')
        exported_count += 1
    
    return exported_count


def export_all_charts(models, leaderboard_data, l1_dims, imgs_dir, timestamp, export_timestamp=True):
    """主要的图表导出函数，自动选择最佳的导出方式"""
    exported_count = 0
    
    try:
        # 首先尝试使用Playwright截取真实网页图表
        try:
            playwright_available = True
            logger.info("Using Playwright for chart export")
        except ImportError:
            playwright_available = False
            logger.warning("Playwright not available, checking for matplotlib...")
            
        if playwright_available:
            exported_count = export_charts_with_playwright(models, leaderboard_data, l1_dims, imgs_dir, timestamp, export_timestamp)
        else:
            # Fallback to matplotlib if Playwright is not available
            try:
                matplotlib.use('Agg')  # Use non-interactive backend
                chart_lib_available = True
                logger.info("Using matplotlib for chart export")
            except ImportError:
                chart_lib_available = False
                logger.warning("Neither Playwright nor matplotlib available, using placeholder files")
            
            if chart_lib_available:
                exported_count = export_charts_with_matplotlib(models, leaderboard_data, l1_dims, imgs_dir, timestamp, export_timestamp)
            else:
                exported_count = export_charts_placeholder(models, imgs_dir, timestamp, export_timestamp)
    
    except Exception as chart_export_error:
        logger.error(f"Error in chart export logic: {chart_export_error}", exc_info=True)
        exported_count = export_charts_placeholder(models, imgs_dir, timestamp, export_timestamp)
    
    return exported_count