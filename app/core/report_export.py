import logging
from pathlib import Path
from datetime import datetime

from app.core.llm import clients
from app.extensions import db
from app.core.utils import generate_leaderboard_data

logger = logging.getLogger('report_export')

data_template = '''各模型综合得分与相应率
模型,得分,相应率
{table_1}
各模型维度得分
模型,{table_2_column}
{table_2_content}
各模型题型数据
模型, 客观题, 主观题
{table_3}
详细数据：
{json_data}'''

def export_report():
    report_path = Path('./exports/reports')
    report_path.mkdir(exist_ok=True, parents=True)
    
    leaderboard_data, l1_dims = generate_leaderboard_data().values()
    
    with open(report_path / datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'w', encoding = 'utf-8') as f:
        f.write('')
    