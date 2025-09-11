#!/usr/bin/env python3

"""
简单测试Playwright连接
"""

from playwright.sync_api import sync_playwright
import time
import os

def test_simple_playwright():
    """简单测试Playwright是否能连接到本地服务器"""
    
    # 临时禁用代理环境变量
    old_http_proxy = os.environ.pop('http_proxy', None)
    old_https_proxy = os.environ.pop('https_proxy', None)
    old_HTTP_PROXY = os.environ.pop('HTTP_PROXY', None)
    old_HTTPS_PROXY = os.environ.pop('HTTPS_PROXY', None)
    
    try:
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
            
            try:
                print("尝试访问 http://localhost:5000/")
                page.goto("http://localhost:5000/", timeout=10000)  # 10秒超时
                
                title = page.title()
                print(f"页面标题: {title}")
                
                # 检查是否有图表元素
                chart_element = page.query_selector('#overall-bar-chart')
                if chart_element:
                    print("找到图表元素 #overall-bar-chart")
                    
                    # 等待一下让图表加载
                    page.wait_for_timeout(3000)
                    
                    # 尝试截图
                    screenshot_path = "./temp/test_chart.png"
                    chart_element.screenshot(path=screenshot_path)
                    print(f"截图保存到: {screenshot_path}")
                else:
                    print("未找到图表元素 #overall-bar-chart")
                    
            except Exception as e:
                print(f"错误: {e}")
            finally:
                browser.close()
    finally:
        # 恢复代理环境变量
        if old_http_proxy:
            os.environ['http_proxy'] = old_http_proxy
        if old_https_proxy:
            os.environ['https_proxy'] = old_https_proxy
        if old_HTTP_PROXY:
            os.environ['HTTP_PROXY'] = old_HTTP_PROXY
        if old_HTTPS_PROXY:
            os.environ['HTTPS_PROXY'] = old_HTTPS_PROXY

if __name__ == "__main__":
    test_simple_playwright()