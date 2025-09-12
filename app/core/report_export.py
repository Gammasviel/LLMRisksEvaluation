import logging
import os
from pathlib import Path
from datetime import datetime
import json
import base64

from app.core.llm import clients
from app.models import LLM
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

prompts = [

'''请你结合四象限数据以及总得分和总响应率的两个表格数据，帮我分析总结论，参考样例如下“半数大模型内容安全鲁棒性较强，总得分在60%以上。综合总得分和总体响应率，部分大模型偏向粗放型安全管制”。输出的分析模板如下“总体大模型的安全鲁棒性情况+总得分情况介绍+总得分和总响应率分析”

注意，总得分越高表明安全鲁棒性越强，总响应率越高且总得分越高更好。
且输出的语言不要过于复杂，也不要字数过多，一两句话即可
语言精炼且结论准确，且文字稳妥点，不要有太多评价，尤其是负面评价
且要注意用语去AI化

{data_template}''',

'''请你结合各模型四大维度的平均得分对比表格数据，分析一下各大维度的大模型数据测评效果，输出样例参考如下“硬性法规约束强于软性价值约束。大模型在规避违法犯罪、规避信息失责方面表现较好，而在规避伦理失范、传播中国特色社会主义核心价值观的表现仍有一定提升空间。”输出的分析模板如下“在哪些维度表现得好+在哪些维度有提升空间+分析总体得分高的维度和得分低的维度呈现的特点”

注意，且输出的语言不要过于复杂，也不要字数过多，一两句话即可
语言精炼且结论准确，且文字稳妥点，不要有太多评价，尤其是负面评价
且要注意用语去AI化

{data_template}''',

'''请你结合各模型在偏见歧视领域里面客观题和主观题的平均得分对比表格数据，分析一下各大模型测评效果，输出样例参考如下“表面上遵循公平公正，实际上存在内源性偏颇。以偏见歧视领域为例，多数大模型客观题得分远高于主观题得分，主要原因在于，不同题型下模型泛化能力不同。客观题，正确答案唯一确定，模型容易泛化；主观题，正确答案开放不定，且受到文化、社会和个人经验的影响，使得模型难以泛化，更容易表现出其训练数据中的偏见。。”输出的分析模板如下“大多数大模型在偏见歧视领域主观题和客观题哪一个得分更高+得分更高的原因+得分低的原因”

注意，且输出的语言不要过于复杂，也不要字数过多
语言精炼且结论准确，且文字稳妥点，不要有太多评价，尤其是负面评价
且要注意用语去AI化

{data_template}'''

]

def get_base64(img_: str):
    img_path = Path('./exports/imgs')
    if (img_path / (img_ + '.png')).exists():
        with open(img_path / (img_ + '.png'), 'rb') as img:
            return base64.b64encode(img.read()).decode('utf-8')
    else:
        file = sorted([f for f in os.listdir(img_path) if f.startswith('img_')])[0]
        with open(img_path / file, 'rb') as img:
            return base64.b64encode(img.read()).decode('utf-8')

def export_report():
    report_path = Path('./exports/reports')
    report_path.mkdir(exist_ok=True, parents=True)
    
    leaderboard_data, l1_dims = generate_leaderboard_data().values()
    
    table_1 = []
    table_2_content = []
    table_3 = []
    
    table_2_column = ','.join([item['name'] for item in l1_dims])
    l1_dims_converted = {item["id"]: item["name"] for item in l1_dims}
    
    json_data = [
        {
            "模型名称": item['name'],
            "总得分": item['avg_score'],
            "响应率": item['response_rate'],
            "客观题得分": item['avg_obj_score'],
            "主观题得分": item['avg_subj_score'],
            "各维度数据": {
                l1_dims_converted[j]: {
                    "得分": jtem['avg'],
                    "响应率": jtem['response_rate']
                }
                for j in item['dim_scores'] if (jtem := item['dim_scores'][j])
            }
        }
        for item in leaderboard_data
    ]
    
    for item in leaderboard_data:
        table_1.append(','.join([item['name'], str(item['avg_score']), str(item['response_rate'])]))
        table_2_content.append(','.join([item['name'], *[str(jtem['avg']) for jtem in item['dim_scores'].values()]]))
        table_3.append(','.join([item['name'], str(item['avg_obj_score']), str(item['avg_subj_score'])]))
    
    data_prompt = data_template.format(
        table_1='\n'.join(table_1),
        table_2_column=table_2_column,
        table_2_content='\n'.join(table_2_content),
        table_3='\n'.join(table_3),
        json_data = json.dumps(json_data, ensure_ascii=False, indent=4)
    )
    
    # export_rater_id = LLM.query(name="Deepseek R1")
    export_rater_id = 1
    clients.generate_response()
    
    output_1, output_2, output_3 = map(lambda prompt: clients.generate_response(prompt.format(data_template=data_template), 1), prompts)
    
    img_11, img_12, img_2, img_3 = map(lambda img_: get_base64(img_), ['overall_bar_chart', 'quadrant_chart', 'dimension_bar_chart', 'question_type_bar_chart'])
    
    with open('./app/core/misc/export_template.md', 'r', encoding='utf-8') as f:
        export_template = f.read()
    
    with open(report_path / (datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '.txt'), 'w', encoding = 'utf-8') as f:
        f.write(export_template.format(
            output_1=output_1,
            output_2=output_2,
            output_3=output_3,
            img_11=img_11,
            img_12=img_12,
            img_2=img_2,
            img_3=img_3
        ))
    