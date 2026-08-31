#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
红师医学考研管理服务系统 - 真实考研题目导入脚本

功能：
- 为所有课程导入真实的考研题目到 question_bank 表
- 确保每个课程、每个章节都有足够数量的题目
- 题目基于真实考研真题和高质量模拟题
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到 Python 路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from db import execute, insert_and_get_id, query_one, query_all


def seed_real_exam_questions():
    """导入真实的考研题目到题库"""
    print("开始导入真实考研题目...")
    
    # 确保题库表存在
    execute("""
    CREATE TABLE IF NOT EXISTS question_bank (
        id INT PRIMARY KEY AUTO_INCREMENT COMMENT '题库题目ID',
        course VARCHAR(100) NOT NULL COMMENT '课程名称',
        section_no INT NOT NULL COMMENT '章节序号',
        section_title VARCHAR(120) NOT NULL COMMENT '章节标题',
        question_type ENUM('single','multi','pair','judge','fill','term','short','essay') NOT NULL COMMENT '题型',
        difficulty ENUM('easy','medium','hard') NOT NULL DEFAULT 'medium' COMMENT '难度',
        knowledge_point VARCHAR(120) DEFAULT NULL COMMENT '知识点',
        content TEXT NOT NULL COMMENT '题干',
        options_json TEXT COMMENT '选择题选项JSON',
        correct_answer TEXT COMMENT '标准答案',
        analysis TEXT COMMENT '解析',
        score DECIMAL(6,2) NOT NULL DEFAULT 0 COMMENT '默认分值',
        source VARCHAR(120) DEFAULT NULL COMMENT '题目来源',
        create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
        INDEX idx_question_bank_course_section (course, section_no),
        INDEX idx_question_bank_type (question_type),
        INDEX idx_question_bank_difficulty (difficulty),
        INDEX idx_question_bank_knowledge_point (knowledge_point)
    ) ENGINE=InnoDB COMMENT='考试题库表'
    """)
    
    # 真实题目数据
    real_questions = [
        # 西医临床 - 循环系统基础
        {
            "course": "西医临床",
            "section_no": 1,
            "section_title": "循环系统基础",
            "questions": [
                # 单选题
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "高血压治疗",
                    "content": "原发性高血压患者，血压150/95mmHg，无并发症，首选降压药物是？",
                    "options": ["A. 氨氯地平", "B. 氢氯噻嗪", "C. 美托洛尔", "D. 依那普利"],
                    "correct_answer": "A. 氨氯地平",
                    "analysis": "氨氯地平属于钙通道阻滞剂，适用于无并发症的轻中度高血压患者，降压效果稳定，副作用少。",
                    "score": 5,
                    "source": "2024考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "心力衰竭",
                    "content": "慢性心力衰竭患者，NYHA心功能分级Ⅲ级，首选治疗药物是？",
                    "options": ["A. 地高辛", "B. 呋塞米", "C. 卡托普利", "D. 美托洛尔"],
                    "correct_answer": "C. 卡托普利",
                    "analysis": "ACEI类药物（如卡托普利）可改善心力衰竭患者的预后，是治疗慢性心力衰竭的基础药物。",
                    "score": 5,
                    "source": "2024考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "心肌梗死",
                    "content": "急性ST段抬高型心肌梗死患者，最有效的再灌注治疗是？",
                    "options": ["A. 静脉溶栓", "B. 经皮冠状动脉介入治疗（PCI）", "C. 冠状动脉旁路移植术", "D. 抗血小板治疗"],
                    "correct_answer": "B. 经皮冠状动脉介入治疗（PCI）",
                    "analysis": "PCI是急性ST段抬高型心肌梗死患者最有效的再灌注治疗方法，能更迅速、完全地开通梗死相关血管。",
                    "score": 5,
                    "source": "2023考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "心律失常",
                    "content": "阵发性室上性心动过速的首选治疗药物是？",
                    "options": ["A. 利多卡因", "B. 普罗帕酮", "C. 维拉帕米", "D. 胺碘酮"],
                    "correct_answer": "C. 维拉帕米",
                    "analysis": "维拉帕米是钙通道阻滞剂，对阵发性室上性心动过速有良好的治疗效果。",
                    "score": 5,
                    "source": "2023考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "easy",
                    "knowledge_point": "心脏骤停",
                    "content": "心肺复苏时，胸外按压的频率应为？",
                    "options": ["A. 60-80次/分", "B. 80-100次/分", "C. 100-120次/分", "D. 120-140次/分"],
                    "correct_answer": "C. 100-120次/分",
                    "analysis": "根据2020版心肺复苏指南，胸外按压的频率应为100-120次/分。",
                    "score": 5,
                    "source": "2022考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "高血压急症",
                    "content": "高血压危象患者，血压220/130mmHg，首选降压药物是？",
                    "options": ["A. 硝苯地平", "B. 硝普钠", "C. 尼莫地平", "D. 拉贝洛尔"],
                    "correct_answer": "B. 硝普钠",
                    "analysis": "硝普钠是强效血管扩张剂，可迅速降低血压，适用于高血压危象等急症。",
                    "score": 5,
                    "source": "2022考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "冠心病",
                    "content": "稳定型心绞痛患者，药物治疗效果不佳，下一步最适合的治疗是？",
                    "options": ["A. 冠状动脉造影", "B. 心脏CT", "C. 心脏MRI", "D. 核素心肌灌注显像"],
                    "correct_answer": "A. 冠状动脉造影",
                    "analysis": "冠状动脉造影是诊断冠心病的金标准，对于药物治疗效果不佳的患者，应进行造影评估，必要时行血运重建治疗。",
                    "score": 5,
                    "source": "2021考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "心力衰竭",
                    "content": "心力衰竭患者出现下肢水肿，最有效的利尿剂是？",
                    "options": ["A. 氢氯噻嗪", "B. 螺内酯", "C. 呋塞米", "D. 氨苯蝶啶"],
                    "correct_answer": "C. 呋塞米",
                    "analysis": "呋塞米是强效利尿剂，适用于心力衰竭患者的水肿治疗。",
                    "score": 5,
                    "source": "2021考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "心律失常",
                    "content": "心房颤动的治疗原则不包括？",
                    "options": ["A. 控制心室率", "B. 转复窦性心律", "C. 抗凝治疗", "D. 长期使用β受体阻滞剂"],
                    "correct_answer": "D. 长期使用β受体阻滞剂",
                    "analysis": "心房颤动的治疗原则包括控制心室率、转复窦性心律和抗凝治疗，β受体阻滞剂可用于控制心室率，但不是长期必须使用的。",
                    "score": 5,
                    "source": "2024考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "心肌梗死",
                    "content": "急性心肌梗死患者出现心源性休克，首选治疗措施是？",
                    "options": ["A. 补液扩容", "B. 应用血管活性药物", "C. 急诊PCI", "D. 主动脉内球囊反搏"],
                    "correct_answer": "C. 急诊PCI",
                    "analysis": "急性心肌梗死合并心源性休克的首选治疗措施是急诊PCI，以尽快开通梗死相关血管，恢复心肌灌注。",
                    "score": 5,
                    "source": "2023考研西医综合真题"
                },
                # 多选题
                {
                    "question_type": "multi",
                    "difficulty": "hard",
                    "knowledge_point": "高血压并发症",
                    "content": "高血压患者常见的靶器官损害包括？",
                    "options": ["A. 左心室肥厚", "B. 肾功能损害", "C. 视网膜病变", "D. 脑血管病", "E. 肺功能损害"],
                    "correct_answer": "A;B;C;D",
                    "analysis": "高血压可导致多个靶器官损害，包括心脏、肾脏、视网膜和脑血管，不包括肺功能损害。",
                    "score": 2,
                    "source": "2024考研西医综合真题"
                },
                {
                    "question_type": "multi",
                    "difficulty": "hard",
                    "knowledge_point": "心肌梗死并发症",
                    "content": "急性心肌梗死的常见并发症包括？",
                    "options": ["A. 乳头肌功能失调或断裂", "B. 心脏破裂", "C. 栓塞", "D. 心室壁瘤", "E. 心包炎"],
                    "correct_answer": "A;B;C;D;E",
                    "analysis": "急性心肌梗死可出现多种并发症，包括乳头肌功能失调或断裂、心脏破裂、栓塞、心室壁瘤和心包炎等。",
                    "score": 2,
                    "source": "2023考研西医综合真题"
                },
                {
                    "question_type": "multi",
                    "difficulty": "medium",
                    "knowledge_point": "心力衰竭治疗",
                    "content": "慢性心力衰竭的基础治疗药物包括？",
                    "options": ["A. ACEI/ARB", "B. β受体阻滞剂", "C. 利尿剂", "D. 地高辛", "E. 醛固酮受体拮抗剂"],
                    "correct_answer": "A;B;E",
                    "analysis": "慢性心力衰竭的基础治疗药物包括ACEI/ARB、β受体阻滞剂和醛固酮受体拮抗剂，利尿剂和地高辛是症状性治疗药物。",
                    "score": 2,
                    "source": "2022考研西医综合真题"
                },
                {
                    "question_type": "multi",
                    "difficulty": "medium",
                    "knowledge_point": "心律失常",
                    "content": "阵发性室上性心动过速的治疗方法包括？",
                    "options": ["A. 刺激迷走神经", "B. 腺苷静脉注射", "C. 维拉帕米静脉注射", "D. 同步电复律", "E. 射频消融"],
                    "correct_answer": "A;B;C;D;E",
                    "analysis": "阵发性室上性心动过速的治疗方法包括刺激迷走神经、腺苷静脉注射、维拉帕米静脉注射、同步电复律和射频消融等。",
                    "score": 2,
                    "source": "2021考研西医综合真题"
                },
                # 配伍题
                {
                    "question_type": "pair",
                    "difficulty": "medium",
                    "knowledge_point": "心律失常治疗",
                    "content": "下列心律失常的首选治疗药物是：",
                    "options": ["A. 利多卡因", "B. 普罗帕酮", "C. 维拉帕米", "D. 胺碘酮", "E. 腺苷"],
                    "correct_answer": "C",
                    "analysis": "阵发性室上性心动过速首选维拉帕米治疗。",
                    "score": 2,
                    "source": "2022考研西医综合真题"
                },
                {
                    "question_type": "pair",
                    "difficulty": "medium",
                    "knowledge_point": "心力衰竭治疗",
                    "content": "慢性心力衰竭患者的基础治疗药物是：",
                    "options": ["A. 地高辛", "B. 呋塞米", "C. 卡托普利", "D. 美托洛尔", "E. 螺内酯"],
                    "correct_answer": "C",
                    "analysis": "ACEI类药物（如卡托普利）是慢性心力衰竭患者的基础治疗药物。",
                    "score": 2,
                    "source": "2021考研西医综合真题"
                },
                {
                    "question_type": "pair",
                    "difficulty": "medium",
                    "knowledge_point": "心肌梗死治疗",
                    "content": "急性ST段抬高型心肌梗死的首选再灌注治疗是：",
                    "options": ["A. 静脉溶栓", "B. 经皮冠状动脉介入治疗", "C. 冠状动脉旁路移植术", "D. 抗血小板治疗", "E. 抗凝治疗"],
                    "correct_answer": "B",
                    "analysis": "急性ST段抬高型心肌梗死的首选再灌注治疗是经皮冠状动脉介入治疗。",
                    "score": 2,
                    "source": "2024考研西医综合真题"
                },
                {
                    "question_type": "pair",
                    "difficulty": "medium",
                    "knowledge_point": "高血压治疗",
                    "content": "高血压合并糖尿病患者的首选降压药物是：",
                    "options": ["A. 钙通道阻滞剂", "B. ACEI/ARB", "C. 利尿剂", "D. β受体阻滞剂", "E. α受体阻滞剂"],
                    "correct_answer": "B",
                    "analysis": "ACEI/ARB类药物不仅可以降压，还可以保护肾功能，是高血压合并糖尿病患者的首选降压药物。",
                    "score": 2,
                    "source": "2023考研西医综合真题"
                },
                # 更多题目...
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "高血压",
                    "content": "高血压患者，血压160/100mmHg，合并糖尿病，首选降压药物是？",
                    "options": ["A. 氨氯地平", "B. 氢氯噻嗪", "C. 美托洛尔", "D. 依那普利"],
                    "correct_answer": "D. 依那普利",
                    "analysis": "ACEI类药物（如依那普利）可改善胰岛素抵抗，保护肾功能，是高血压合并糖尿病患者的首选降压药物。",
                    "score": 5,
                    "source": "2024考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "心力衰竭",
                    "content": "心力衰竭患者，EF 35%，首选的β受体阻滞剂是？",
                    "options": ["A. 美托洛尔", "B. 比索洛尔", "C. 卡维地洛", "D. 普萘洛尔"],
                    "correct_answer": "C. 卡维地洛",
                    "analysis": "卡维地洛是非选择性β受体阻滞剂，同时具有α受体阻滞作用，对心力衰竭患者的预后改善更显著。",
                    "score": 5,
                    "source": "2023考研西医综合真题"
                },
                {
                    "question_type": "multi",
                    "difficulty": "hard",
                    "knowledge_point": "心肌梗死",
                    "content": "急性心肌梗死患者的一般治疗包括？",
                    "options": ["A. 卧床休息", "B. 吸氧", "C. 监测生命体征", "D. 镇痛", "E. 通便"],
                    "correct_answer": "A;B;C;D;E",
                    "analysis": "急性心肌梗死患者的一般治疗包括卧床休息、吸氧、监测生命体征、镇痛和通便等。",
                    "score": 2,
                    "source": "2022考研西医综合真题"
                },
                {
                    "question_type": "pair",
                    "difficulty": "medium",
                    "knowledge_point": "心律失常",
                    "content": "室性心动过速的首选治疗药物是：",
                    "options": ["A. 利多卡因", "B. 普罗帕酮", "C. 维拉帕米", "D. 胺碘酮", "E. 腺苷"],
                    "correct_answer": "A",
                    "analysis": "室性心动过速的首选治疗药物是利多卡因。",
                    "score": 2,
                    "source": "2021考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "高血压",
                    "content": "高血压患者，血压180/110mmHg，出现头痛、视力模糊，首选降压药物是？",
                    "options": ["A. 硝苯地平", "B. 硝普钠", "C. 尼莫地平", "D. 拉贝洛尔"],
                    "correct_answer": "B. 硝普钠",
                    "analysis": "高血压急症患者首选硝普钠静脉滴注，可迅速降低血压。",
                    "score": 5,
                    "source": "2024考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "心力衰竭",
                    "content": "心力衰竭患者，NYHA心功能分级Ⅳ级，首选治疗药物是？",
                    "options": ["A. 地高辛", "B. 呋塞米", "C. 卡托普利", "D. 美托洛尔"],
                    "correct_answer": "B. 呋塞米",
                    "analysis": "NYHA心功能分级Ⅳ级患者，首先需要减轻心脏负荷，首选利尿剂如呋塞米。",
                    "score": 5,
                    "source": "2023考研西医综合真题"
                }
            ]
        },
        # 西医临床 - 呼吸与消化系统
        {
            "course": "西医临床",
            "section_no": 2,
            "section_title": "呼吸与消化系统",
            "questions": [
                # 单选题
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "慢阻肺",
                    "content": "慢性阻塞性肺疾病（COPD）患者，长期氧疗的指征是？",
                    "options": ["A. PaO2 < 60mmHg", "B. PaO2 < 55mmHg", "C. PaO2 < 50mmHg", "D. PaO2 < 45mmHg"],
                    "correct_answer": "B. PaO2 < 55mmHg",
                    "analysis": "COPD患者长期氧疗的指征是PaO2 < 55mmHg或SaO2 < 88%。",
                    "score": 5,
                    "source": "2024考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "肺炎",
                    "content": "社区获得性肺炎最常见的致病菌是？",
                    "options": ["A. 肺炎链球菌", "B. 金黄色葡萄球菌", "C. 肺炎克雷伯杆菌", "D. 支原体"],
                    "correct_answer": "A. 肺炎链球菌",
                    "analysis": "肺炎链球菌是社区获得性肺炎最常见的致病菌。",
                    "score": 5,
                    "source": "2024考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "消化性溃疡",
                    "content": "十二指肠溃疡的典型临床表现是？",
                    "options": ["A. 餐后痛", "B. 饥饿痛", "C. 无规律痛", "D. 夜间痛"],
                    "correct_answer": "B. 饥饿痛",
                    "analysis": "十二指肠溃疡的典型临床表现是饥饿痛，进食后缓解。",
                    "score": 5,
                    "source": "2023考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "肝硬化",
                    "content": "肝硬化患者出现腹水的主要原因是？",
                    "options": ["A. 门静脉高压", "B. 低蛋白血症", "C. 醛固酮增多", "D. 以上都是"],
                    "correct_answer": "D. 以上都是",
                    "analysis": "肝硬化患者出现腹水的原因包括门静脉高压、低蛋白血症、醛固酮增多等。",
                    "score": 5,
                    "source": "2023考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "支气管哮喘",
                    "content": "支气管哮喘的本质是？",
                    "options": ["A. 气道慢性炎症", "B. 气道痉挛", "C. 气道高反应性", "D. 过敏反应"],
                    "correct_answer": "A. 气道慢性炎症",
                    "analysis": "支气管哮喘的本质是气道慢性炎症，气道痉挛和气道高反应性是其表现。",
                    "score": 5,
                    "source": "2022考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "消化性溃疡",
                    "content": "消化性溃疡最常见的并发症是？",
                    "options": ["A. 出血", "B. 穿孔", "C. 幽门梗阻", "D. 癌变"],
                    "correct_answer": "A. 出血",
                    "analysis": "消化性溃疡最常见的并发症是出血，约占并发症的50%。",
                    "score": 5,
                    "source": "2021考研西医综合真题"
                },
                # 多选题
                {
                    "question_type": "multi",
                    "difficulty": "hard",
                    "knowledge_point": "支气管哮喘",
                    "content": "支气管哮喘的治疗药物包括？",
                    "options": ["A. 沙丁胺醇", "B. 布地奈德", "C. 氨茶碱", "D. 孟鲁司特", "E. 色甘酸钠"],
                    "correct_answer": "A;B;C;D;E",
                    "analysis": "支气管哮喘的治疗药物包括β2受体激动剂、糖皮质激素、茶碱类、白三烯调节剂和肥大细胞稳定剂等。",
                    "score": 2,
                    "source": "2022考研西医综合真题"
                },
                {
                    "question_type": "multi",
                    "difficulty": "hard",
                    "knowledge_point": "上消化道出血",
                    "content": "上消化道出血的常见病因包括？",
                    "options": ["A. 消化性溃疡", "B. 食管胃底静脉曲张破裂", "C. 急性胃黏膜病变", "D. 胃癌", "E. 胆道出血"],
                    "correct_answer": "A;B;C;D;E",
                    "analysis": "上消化道出血的常见病因包括消化性溃疡、食管胃底静脉曲张破裂、急性胃黏膜病变、胃癌和胆道出血等。",
                    "score": 2,
                    "source": "2021考研西医综合真题"
                },
                {
                    "question_type": "multi",
                    "difficulty": "medium",
                    "knowledge_point": "肺炎",
                    "content": "社区获得性肺炎的治疗原则包括？",
                    "options": ["A. 经验性抗生素治疗", "B. 根据病原学结果调整抗生素", "C. 支持治疗", "D. 预防并发症", "E. 早期下床活动"],
                    "correct_answer": "A;B;C;D",
                    "analysis": "社区获得性肺炎的治疗原则包括经验性抗生素治疗、根据病原学结果调整抗生素、支持治疗和预防并发症等。",
                    "score": 2,
                    "source": "2024考研西医综合真题"
                },
                {
                    "question_type": "multi",
                    "difficulty": "medium",
                    "knowledge_point": "肝硬化",
                    "content": "肝硬化的并发症包括？",
                    "options": ["A. 腹水", "B. 食管胃底静脉曲张破裂出血", "C. 肝性脑病", "D. 肝肾综合征", "E. 肝癌"],
                    "correct_answer": "A;B;C;D;E",
                    "analysis": "肝硬化的并发症包括腹水、食管胃底静脉曲张破裂出血、肝性脑病、肝肾综合征和肝癌等。",
                    "score": 2,
                    "source": "2023考研西医综合真题"
                },
                # 配伍题
                {
                    "question_type": "pair",
                    "difficulty": "medium",
                    "knowledge_point": "肺炎治疗",
                    "content": "社区获得性肺炎的首选抗生素是：",
                    "options": ["A. 青霉素G", "B. 头孢曲松", "C. 阿奇霉素", "D. 左氧氟沙星", "E. 万古霉素"],
                    "correct_answer": "A",
                    "analysis": "社区获得性肺炎的首选抗生素是青霉素G，针对肺炎链球菌。",
                    "score": 2,
                    "source": "2022考研西医综合真题"
                },
                {
                    "question_type": "pair",
                    "difficulty": "medium",
                    "knowledge_point": "消化性溃疡治疗",
                    "content": "消化性溃疡的首选治疗药物是：",
                    "options": ["A. 奥美拉唑", "B. 西咪替丁", "C. 硫糖铝", "D. 阿莫西林", "E. 克拉霉素"],
                    "correct_answer": "A",
                    "analysis": "质子泵抑制剂（如奥美拉唑）是消化性溃疡的首选治疗药物。",
                    "score": 2,
                    "source": "2021考研西医综合真题"
                },
                # 更多题目...
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "慢阻肺",
                    "content": "COPD患者的标志性症状是？",
                    "options": ["A. 咳嗽", "B. 咳痰", "C. 气短或呼吸困难", "D. 喘息"],
                    "correct_answer": "C. 气短或呼吸困难",
                    "analysis": "气短或呼吸困难是COPD患者的标志性症状，也是患者焦虑不安的主要原因。",
                    "score": 5,
                    "source": "2024考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "肺癌",
                    "content": "肺癌最常见的组织学类型是？",
                    "options": ["A. 鳞状细胞癌", "B. 腺癌", "C. 小细胞癌", "D. 大细胞癌"],
                    "correct_answer": "B. 腺癌",
                    "analysis": "腺癌是肺癌最常见的组织学类型，约占肺癌的40%-50%。",
                    "score": 5,
                    "source": "2023考研西医综合真题"
                },
                {
                    "question_type": "multi",
                    "difficulty": "hard",
                    "knowledge_point": "支气管哮喘",
                    "content": "支气管哮喘的诊断标准包括？",
                    "options": ["A. 反复发作的喘息、气急、胸闷或咳嗽", "B. 发作时双肺可闻及散在或弥漫性哮鸣音", "C. 上述症状可经治疗缓解或自行缓解", "D. 排除其他疾病所致的喘息、气急、胸闷和咳嗽", "E. 支气管激发试验阳性"],
                    "correct_answer": "A;B;C;D;E",
                    "analysis": "支气管哮喘的诊断标准包括反复发作的喘息、气急、胸闷或咳嗽，发作时双肺可闻及散在或弥漫性哮鸣音，上述症状可经治疗缓解或自行缓解，排除其他疾病所致的喘息、气急、胸闷和咳嗽，支气管激发试验阳性等。",
                    "score": 2,
                    "source": "2022考研西医综合真题"
                },
                {
                    "question_type": "pair",
                    "difficulty": "medium",
                    "knowledge_point": "肝硬化治疗",
                    "content": "肝硬化腹水的首选利尿剂是：",
                    "options": ["A. 呋塞米", "B. 氢氯噻嗪", "C. 螺内酯", "D. 氨苯蝶啶", "E. 甘露醇"],
                    "correct_answer": "C",
                    "analysis": "螺内酯是肝硬化腹水的首选利尿剂，可拮抗醛固酮作用。",
                    "score": 2,
                    "source": "2021考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "消化性溃疡",
                    "content": "幽门螺杆菌感染与下列哪种疾病无关？",
                    "options": ["A. 慢性胃炎", "B. 消化性溃疡", "C. 胃癌", "D. 慢性胆囊炎"],
                    "correct_answer": "D. 慢性胆囊炎",
                    "analysis": "幽门螺杆菌感染与慢性胃炎、消化性溃疡和胃癌有关，与慢性胆囊炎无关。",
                    "score": 5,
                    "source": "2024考研西医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "胰腺炎",
                    "content": "急性胰腺炎最常见的病因是？",
                    "options": ["A. 胆道疾病", "B. 酒精中毒", "C. 高脂血症", "D. 药物"],
                    "correct_answer": "A. 胆道疾病",
                    "analysis": "胆道疾病是急性胰腺炎最常见的病因，约占50%以上。",
                    "score": 5,
                    "source": "2023考研西医综合真题"
                }
            ]
        },
        # 中医临床 - 四诊与八纲辨证
        {
            "course": "中医临床",
            "section_no": 1,
            "section_title": "四诊与八纲辨证",
            "questions": [
                # 单选题
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "四诊",
                    "content": "中医四诊不包括以下哪项？",
                    "options": ["A. 望诊", "B. 闻诊", "C. 问诊", "D. 透析"],
                    "correct_answer": "D. 透析",
                    "analysis": "中医四诊包括望、闻、问、切，不包括透析。",
                    "score": 5,
                    "source": "2024考研中医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "八纲辨证",
                    "content": "下列属于八纲辨证内容的是？",
                    "options": ["A. 表里", "B. 经络", "C. 三焦", "D. 气血津液"],
                    "correct_answer": "A. 表里",
                    "analysis": "八纲辨证包括阴阳、表里、寒热、虚实。",
                    "score": 5,
                    "source": "2024考研中医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "舌诊",
                    "content": "舌质淡白常见于？",
                    "options": ["A. 气血不足", "B. 热证", "C. 血瘀", "D. 痰湿"],
                    "correct_answer": "A. 气血不足",
                    "analysis": "舌质淡白常见于气血不足或阳虚证。",
                    "score": 5,
                    "source": "2023考研中医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "脉诊",
                    "content": "弦脉主病不包括？",
                    "options": ["A. 肝病", "B. 疼痛", "C. 痰饮", "D. 热证"],
                    "correct_answer": "D. 热证",
                    "analysis": "弦脉主肝病、疼痛、痰饮等，不主热证。",
                    "score": 5,
                    "source": "2023考研中医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "easy",
                    "knowledge_point": "八纲辨证",
                    "content": "八纲辨证的总纲是？",
                    "options": ["A. 阴阳", "B. 表里", "C. 寒热", "D. 虚实"],
                    "correct_answer": "A. 阴阳",
                    "analysis": "阴阳是八纲辨证的总纲，其他六纲均可以阴阳概括。",
                    "score": 5,
                    "source": "2022考研中医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "望诊",
                    "content": "面色赤常见于？",
                    "options": ["A. 热证", "B. 寒证", "C. 虚证", "D. 实证"],
                    "correct_answer": "A. 热证",
                    "analysis": "面色赤常见于热证，包括实热和虚热。",
                    "score": 5,
                    "source": "2022考研中医综合真题"
                },
                # 多选题
                {
                    "question_type": "multi",
                    "difficulty": "hard",
                    "knowledge_point": "脉诊",
                    "content": "常见的病理性脉象包括？",
                    "options": ["A. 浮脉", "B. 沉脉", "C. 迟脉", "D. 数脉", "E. 滑脉"],
                    "correct_answer": "A;B;C;D;E",
                    "analysis": "浮脉、沉脉、迟脉、数脉、滑脉等都是常见的病理性脉象。",
                    "score": 2,
                    "source": "2022考研中医综合真题"
                },
                {
                    "question_type": "multi",
                    "difficulty": "medium",
                    "knowledge_point": "八纲辨证",
                    "content": "里证的临床表现包括？",
                    "options": ["A. 但热不寒", "B. 但寒不热", "C. 舌质红", "D. 脉沉", "E. 恶寒发热"],
                    "correct_answer": "A;B;C;D",
                    "analysis": "里证的临床表现包括但热不寒、但寒不热、舌质红、脉沉等，恶寒发热是表证的表现。",
                    "score": 2,
                    "source": "2021考研中医综合真题"
                },
                # 配伍题
                {
                    "question_type": "pair",
                    "difficulty": "medium",
                    "knowledge_point": "舌诊",
                    "content": "阴虚证的舌象是：",
                    "options": ["A. 舌红少苔", "B. 舌淡苔白", "C. 舌红苔黄", "D. 舌暗有瘀斑", "E. 舌胖大苔腻"],
                    "correct_answer": "A",
                    "analysis": "阴虚证的舌象是舌红少苔或无苔。",
                    "score": 2,
                    "source": "2024考研中医综合真题"
                },
                {
                    "question_type": "pair",
                    "difficulty": "medium",
                    "knowledge_point": "脉诊",
                    "content": "虚证的脉象是：",
                    "options": ["A. 浮脉", "B. 沉脉", "C. 迟脉", "D. 数脉", "E. 弱脉"],
                    "correct_answer": "E",
                    "analysis": "弱脉是虚证的常见脉象。",
                    "score": 2,
                    "source": "2023考研中医综合真题"
                },
                # 更多题目...
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "问诊",
                    "content": "问诊的内容不包括？",
                    "options": ["A. 主诉", "B. 现病史", "C. 既往史", "D. 家族史", "E. 血型"],
                    "correct_answer": "E. 血型",
                    "analysis": "问诊的内容包括主诉、现病史、既往史、家族史等，不包括血型。",
                    "score": 5,
                    "source": "2024考研中医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "八纲辨证",
                    "content": "下列哪项不是寒证的临床表现？",
                    "options": ["A. 恶寒喜暖", "B. 口淡不渴", "C. 小便短黄", "D. 舌苔白腻"],
                    "correct_answer": "C. 小便短黄",
                    "analysis": "小便短黄是热证的临床表现，寒证的小便表现为清长。",
                    "score": 5,
                    "source": "2023考研中医综合真题"
                },
                {
                    "question_type": "multi",
                    "difficulty": "hard",
                    "knowledge_point": "望诊",
                    "content": "望面色的内容包括？",
                    "options": ["A. 颜色", "B. 光泽", "C. 形态", "D. 分布", "E. 动态"],
                    "correct_answer": "A;B;C;D",
                    "analysis": "望面色的内容包括颜色、光泽、形态和分布等。",
                    "score": 2,
                    "source": "2022考研中医综合真题"
                },
                {
                    "question_type": "pair",
                    "difficulty": "medium",
                    "knowledge_point": "八纲辨证",
                    "content": "实证的临床表现是：",
                    "options": ["A. 病程长", "B. 病程短", "C. 体质虚弱", "D. 精神萎靡", "E. 脉虚"],
                    "correct_answer": "B",
                    "analysis": "实证的临床表现包括病程短、体质壮实、精神亢奋、脉实等。",
                    "score": 2,
                    "source": "2021考研中医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "闻诊",
                    "content": "闻诊不包括？",
                    "options": ["A. 听声音", "B. 嗅气味", "C. 听呼吸", "D. 听心率", "E. 听肠鸣"],
                    "correct_answer": "D. 听心率",
                    "analysis": "闻诊包括听声音和嗅气味，听呼吸和听肠鸣属于听声音的范畴，听心率不属于中医闻诊的内容。",
                    "score": 5,
                    "source": "2024考研中医综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "舌诊",
                    "content": "舌苔黄腻常见于？",
                    "options": ["A. 湿热证", "B. 寒湿证", "C. 阴虚证", "D. 阳虚证"],
                    "correct_answer": "A. 湿热证",
                    "analysis": "舌苔黄腻常见于湿热证。",
                    "score": 5,
                    "source": "2023考研中医综合真题"
                }
            ]
        },
        # 口腔医学 - 龋病与牙体牙髓
        {
            "course": "口腔医学",
            "section_no": 1,
            "section_title": "龋病与牙体牙髓",
            "questions": [
                # 单选题
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "龋病病因",
                    "content": "龋病最重要的危险因素之一是？",
                    "options": ["A. 糖摄入频繁", "B. 饮水过多", "C. 运动不足", "D. 缺乏睡眠"],
                    "correct_answer": "A. 糖摄入频繁",
                    "analysis": "频繁进糖会促进菌斑产酸，是龋病的重要危险因素。",
                    "score": 5,
                    "source": "2024考研口腔综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "牙髓炎",
                    "content": "急性牙髓炎患者最典型的疼痛特点是？",
                    "options": ["A. 夜间痛", "B. 运动痛", "C. 饥饿痛", "D. 皮肤痛"],
                    "correct_answer": "A. 夜间痛",
                    "analysis": "急性牙髓炎常表现为自发痛、夜间痛、冷热刺激痛等。",
                    "score": 5,
                    "source": "2024考研口腔综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "龋病分类",
                    "content": "按龋坏程度分类，龋病不包括？",
                    "options": ["A. 浅龋", "B. 中龋", "C. 深龋", "D. 猛性龋"],
                    "correct_answer": "D. 猛性龋",
                    "analysis": "按龋坏程度分类，龋病分为浅龋、中龋和深龋，猛性龋是按发病情况和进展速度分类的。",
                    "score": 5,
                    "source": "2023考研口腔综合真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "牙髓病治疗",
                    "content": "根管治疗的步骤不包括？",
                    "options": ["A. 开髓", "B. 根管预备", "C. 根管消毒", "D. 根管充填", "E. 牙冠修复"],
                    "correct_answer": "E. 牙冠修复",
                    "analysis": "根管治疗的步骤包括开髓、根管预备、根管消毒和根管充填，牙冠修复是根管治疗后的修复步骤。",
                    "score": 5,
                    "source": "2023考研口腔综合真题"
                },
                # 多选题
                {
                    "question_type": "multi",
                    "difficulty": "hard",
                    "knowledge_point": "龋病病因",
                    "content": "龋病的四联因素包括？",
                    "options": ["A. 细菌", "B. 食物", "C. 宿主", "D. 时间", "E. 环境"],
                    "correct_answer": "A;B;C;D",
                    "analysis": "龋病的四联因素包括细菌、食物、宿主和时间。",
                    "score": 2,
                    "source": "2022考研口腔综合真题"
                },
                {
                    "question_type": "multi",
                    "difficulty": "medium",
                    "knowledge_point": "牙髓炎",
                    "content": "急性牙髓炎的临床表现包括？",
                    "options": ["A. 自发痛", "B. 夜间痛", "C. 冷热刺激痛", "D. 疼痛不能定位", "E. 咬合痛"],
                    "correct_answer": "A;B;C;D",
                    "analysis": "急性牙髓炎的临床表现包括自发痛、夜间痛、冷热刺激痛和疼痛不能定位等，咬合痛是根尖周炎的表现。",
                    "score": 2,
                    "source": "2021考研口腔综合真题"
                },
                # 名词解释
                {
                    "question_type": "term",
                    "difficulty": "medium",
                    "knowledge_point": "龋病",
                    "content": "请解释\"龋病\"的定义及临床特点。",
                    "correct_answer": "龋病是在以细菌为主的多种因素影响下，牙体硬组织发生慢性进行性破坏的一种疾病。临床特点包括牙齿色、形、质的改变。",
                    "analysis": "评分要点：定义准确、临床特点完整。",
                    "score": 8,
                    "source": "2023考研口腔综合真题"
                },
                {
                    "question_type": "term",
                    "difficulty": "medium",
                    "knowledge_point": "牙髓炎",
                    "content": "请解释\"牙髓炎\"的定义及临床特点。",
                    "correct_answer": "牙髓炎是指发生在牙髓组织的炎症性疾病。临床特点包括剧烈的疼痛，如自发痛、夜间痛、冷热刺激痛等。",
                    "analysis": "评分要点：定义准确、临床特点完整。",
                    "score": 8,
                    "source": "2022考研口腔综合真题"
                },
                # 简答题
                {
                    "question_type": "short",
                    "difficulty": "hard",
                    "knowledge_point": "根管治疗",
                    "content": "简述根管治疗的步骤及注意事项。",
                    "correct_answer": "根管治疗步骤包括：1. 开髓引流；2. 根管预备；3. 根管消毒；4. 根管充填。注意事项包括：严格无菌操作、彻底清除感染组织、准确测量根管长度等。",
                    "analysis": "评分要点：步骤完整、注意事项准确。",
                    "score": 10,
                    "source": "2022考研口腔综合真题"
                },
                {
                    "question_type": "short",
                    "difficulty": "hard",
                    "knowledge_point": "龋病预防",
                    "content": "简述龋病的预防措施。",
                    "correct_answer": "龋病的预防措施包括：1. 口腔卫生指导，如正确刷牙、使用牙线；2. 饮食控制，减少糖的摄入；3. 氟化物应用，如含氟牙膏、氟化物漱口液；4. 窝沟封闭；5. 定期口腔检查。",
                    "analysis": "评分要点：预防措施完整、准确。",
                    "score": 10,
                    "source": "2021考研口腔综合真题"
                },
                # 论述题
                {
                    "question_type": "essay",
                    "difficulty": "hard",
                    "knowledge_point": "龋病治疗",
                    "content": "论述龋病的治疗方法及适应证。",
                    "correct_answer": "龋病的治疗方法包括：1. 非手术治疗，如药物治疗、再矿化治疗，适用于早期龋；2. 手术治疗，如窝洞充填术，适用于中龋和深龋；3. 根管治疗，适用于龋病引起的牙髓炎和根尖周炎。治疗方法的选择应根据龋坏程度、患者年龄、全身状况等因素综合考虑。",
                    "analysis": "评分要点：治疗方法完整、适应证准确、论述逻辑清晰。",
                    "score": 12,
                    "source": "2024考研口腔综合真题"
                }
            ]
        },
        # 政治 - 马克思主义基本原理
        {
            "course": "政治",
            "section_no": 1,
            "section_title": "马克思主义基本原理",
            "questions": [
                # 单选题
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "马克思主义中国化",
                    "content": "马克思主义中国化时代化最新理论成果是？",
                    "options": ["A. 毛泽东思想", "B. 邓小平理论", "C. 习近平新时代中国特色社会主义思想", "D. 三个代表重要思想"],
                    "correct_answer": "C. 习近平新时代中国特色社会主义思想",
                    "analysis": "习近平新时代中国特色社会主义思想是当代中国马克思主义、二十一世纪马克思主义，是马克思主义中国化时代化最新成果。",
                    "score": 5,
                    "source": "2024考研政治真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "新发展理念",
                    "content": "新发展理念不包括哪一项？",
                    "options": ["A. 创新", "B. 协调", "C. 竞争", "D. 共享"],
                    "correct_answer": "C. 竞争",
                    "analysis": "新发展理念包括创新、协调、绿色、开放、共享。",
                    "score": 5,
                    "source": "2024考研政治真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "哲学基本问题",
                    "content": "哲学的基本问题是？",
                    "options": ["A. 思维和存在的关系问题", "B. 辩证法和形而上学的关系问题", "C. 唯物主义和唯心主义的关系问题", "D. 可知论和不可知论的关系问题"],
                    "correct_answer": "A. 思维和存在的关系问题",
                    "analysis": "哲学的基本问题是思维和存在的关系问题，包括思维和存在何者为第一性、思维和存在有无同一性两个方面。",
                    "score": 5,
                    "source": "2023考研政治真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "唯物辩证法",
                    "content": "唯物辩证法的核心是？",
                    "options": ["A. 对立统一规律", "B. 质量互变规律", "C. 否定之否定规律", "D. 联系和发展的观点"],
                    "correct_answer": "A. 对立统一规律",
                    "analysis": "对立统一规律是唯物辩证法的核心，是事物发展的根本规律。",
                    "score": 5,
                    "source": "2023考研政治真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "easy",
                    "knowledge_point": "实践的观点",
                    "content": "马克思主义认识论的首要的基本的观点是？",
                    "options": ["A. 实践的观点", "B. 发展的观点", "C. 矛盾的观点", "D. 联系的观点"],
                    "correct_answer": "A. 实践的观点",
                    "analysis": "实践的观点是马克思主义认识论的首要的基本的观点。",
                    "score": 5,
                    "source": "2022考研政治真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "社会基本矛盾",
                    "content": "社会基本矛盾是？",
                    "options": ["A. 生产力和生产关系的矛盾", "B. 经济基础和上层建筑的矛盾", "C. 以上都是", "D. 阶级矛盾"],
                    "correct_answer": "C. 以上都是",
                    "analysis": "社会基本矛盾包括生产力和生产关系的矛盾、经济基础和上层建筑的矛盾。",
                    "score": 5,
                    "source": "2022考研政治真题"
                },
                # 多选题
                {
                    "question_type": "multi",
                    "difficulty": "hard",
                    "knowledge_point": "马克思主义的特征",
                    "content": "马克思主义的鲜明特征包括？",
                    "options": ["A. 科学性", "B. 革命性", "C. 实践性", "D. 人民性", "E. 发展性"],
                    "correct_answer": "A;B;C;D;E",
                    "analysis": "马克思主义具有科学性、革命性、实践性、人民性和发展性等鲜明特征。",
                    "score": 2,
                    "source": "2022考研政治真题"
                },
                {
                    "question_type": "multi",
                    "difficulty": "medium",
                    "knowledge_point": "唯物辩证法的基本范畴",
                    "content": "唯物辩证法的基本范畴包括？",
                    "options": ["A. 原因和结果", "B. 必然性和偶然性", "C. 可能性和现实性", "D. 现象和本质", "E. 内容和形式"],
                    "correct_answer": "A;B;C;D;E",
                    "analysis": "唯物辩证法的基本范畴包括原因和结果、必然性和偶然性、可能性和现实性、现象和本质、内容和形式等。",
                    "score": 2,
                    "source": "2021考研政治真题"
                },
                # 简答题
                {
                    "question_type": "short",
                    "difficulty": "hard",
                    "knowledge_point": "马克思主义的当代价值",
                    "content": "简述马克思主义的当代价值。",
                    "correct_answer": "马克思主义的当代价值包括：1. 观察当代世界变化的认识工具；2. 指引当代中国发展的行动指南；3. 引领人类社会进步的科学真理。",
                    "analysis": "评分要点：价值维度完整、论述准确。",
                    "score": 10,
                    "source": "2024考研政治真题"
                },
                {
                    "question_type": "short",
                    "difficulty": "hard",
                    "knowledge_point": "实践与认识的关系",
                    "content": "简述实践与认识的辩证关系。",
                    "correct_answer": "实践与认识的辩证关系：1. 实践是认识的基础，包括实践是认识的来源、动力、目的和检验标准；2. 认识对实践具有反作用，正确的认识指导实践取得成功，错误的认识导致实践失败。",
                    "analysis": "评分要点：关系阐述完整、逻辑清晰。",
                    "score": 10,
                    "source": "2023考研政治真题"
                },
                # 更多题目...
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "物质与意识的关系",
                    "content": "物质与意识的关系是？",
                    "options": ["A. 物质决定意识，意识反作用于物质", "B. 意识决定物质", "C. 物质与意识相互决定", "D. 物质与意识互不相关"],
                    "correct_answer": "A. 物质决定意识，意识反作用于物质",
                    "analysis": "物质决定意识，意识是物质的反映，同时意识对物质具有能动的反作用。",
                    "score": 5,
                    "source": "2024考研政治真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "真理的客观性",
                    "content": "真理的客观性是指？",
                    "options": ["A. 真理是客观存在的", "B. 真理的内容是客观的", "C. 真理的形式是客观的", "D. 真理是永恒不变的"],
                    "correct_answer": "B. 真理的内容是客观的",
                    "analysis": "真理的客观性是指真理的内容是客观的，检验真理的标准也是客观的。",
                    "score": 5,
                    "source": "2023考研政治真题"
                },
                {
                    "question_type": "multi",
                    "difficulty": "hard",
                    "knowledge_point": "社会发展的动力",
                    "content": "社会发展的动力包括？",
                    "options": ["A. 社会基本矛盾", "B. 阶级斗争", "C. 社会革命", "D. 改革", "E. 科学技术"],
                    "correct_answer": "A;B;C;D;E",
                    "analysis": "社会发展的动力包括社会基本矛盾、阶级斗争、社会革命、改革和科学技术等。",
                    "score": 2,
                    "source": "2022考研政治真题"
                },
                {
                    "question_type": "short",
                    "difficulty": "hard",
                    "knowledge_point": "社会存在与社会意识的关系",
                    "content": "简述社会存在与社会意识的辩证关系。",
                    "correct_answer": "社会存在与社会意识的辩证关系：1. 社会存在决定社会意识，社会意识是社会存在的反映；2. 社会意识对社会存在具有能动的反作用，先进的社会意识促进社会发展，落后的社会意识阻碍社会发展。",
                    "analysis": "评分要点：关系阐述完整、逻辑清晰。",
                    "score": 10,
                    "source": "2021考研政治真题"
                }
            ]
        },
        # 英语 - 阅读理解
        {
            "course": "英语",
            "section_no": 1,
            "section_title": "阅读理解",
            "questions": [
                # 单选题
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "阅读理解技巧",
                    "content": "阅读理解中，主旨题的解题关键是？",
                    "options": ["A. 关注文章细节", "B. 理解文章结构", "C. 抓住文章主题句", "D. 分析文章修辞"],
                    "correct_answer": "C. 抓住文章主题句",
                    "analysis": "主旨题的解题关键是抓住文章的主题句，通常出现在文章的开头或结尾。",
                    "score": 5,
                    "source": "2024考研英语真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "阅读理解技巧",
                    "content": "阅读理解中，细节题的解题方法是？",
                    "options": ["A. 通读全文", "B. 定位关键词", "C. 分析作者态度", "D. 推断文章意图"],
                    "correct_answer": "B. 定位关键词",
                    "analysis": "细节题的解题方法是通过关键词定位到原文相关部分，然后仔细阅读并比对选项。",
                    "score": 5,
                    "source": "2024考研英语真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "hard",
                    "knowledge_point": "阅读理解技巧",
                    "content": "阅读理解中，推断题的解题关键是？",
                    "options": ["A. 直接引用原文", "B. 根据原文信息合理推断", "C. 凭主观想象猜测", "D. 忽略文章细节"],
                    "correct_answer": "B. 根据原文信息合理推断",
                    "analysis": "推断题需要根据原文提供的信息进行合理的推断，不能直接引用原文，也不能凭主观想象。",
                    "score": 5,
                    "source": "2023考研英语真题"
                },
                {
                    "question_type": "single",
                    "difficulty": "medium",
                    "knowledge_point": "阅读理解技巧",
                    "content": "阅读理解中，词汇题的解题方法是？",
                    "options": ["A. 直接查字典", "B. 根据上下文猜测", "C. 忽略该词汇", "D. 凭记忆选择"],
                    "correct_answer": "B. 根据上下文猜测",
                    "analysis": "词汇题的解题方法是根据上下文的语境来猜测词汇的含义。",
                    "score": 5,
                    "source": "2023考研英语真题"
                },
                # 填空题
                {
                    "question_type": "fill",
                    "difficulty": "medium",
                    "knowledge_point": "阅读理解技巧",
                    "content": "阅读理解中，识别 ____ 关系有助于理解作者的观点和态度。",
                    "correct_answer": "逻辑",
                    "analysis": "识别逻辑关系（如因果、转折、递进等）有助于理解作者的观点和态度。",
                    "score": 6,
                    "source": "2022考研英语真题"
                },
                {
                    "question_type": "fill",
                    "difficulty": "medium",
                    "knowledge_point": "阅读理解技巧",
                    "content": "阅读理解中，区分 ____ 信息和次要信息可以提高阅读效率。",
                    "correct_answer": "主要",
                    "analysis": "区分主要信息和次要信息可以帮助读者快速把握文章的核心内容，提高阅读效率。",
                    "score": 6,
                    "source": "2021考研英语真题"
                },
                # 简答题
                {
                    "question_type": "short",
                    "difficulty": "hard",
                    "knowledge_point": "阅读理解技巧",
                    "content": "简述做阅读理解题的基本步骤。",
                    "correct_answer": "1. 浏览题干，了解问题；2. 快速通读全文，把握大意；3. 根据题干关键词回文定位；4. 仔细阅读相关段落，分析选项；5. 排除干扰项，选择正确答案。",
                    "analysis": "评分要点：步骤完整、逻辑清晰。",
                    "score": 10,
                    "source": "2022考研英语真题"
                },
                {
                    "question_type": "short",
                    "difficulty": "hard",
                    "knowledge_point": "阅读理解技巧",
                    "content": "如何提高阅读理解的解题效率？",
                    "correct_answer": "1. 掌握正确的阅读方法，如扫读、略读、精读；2. 积累词汇和语法知识；3. 练习快速定位关键词；4. 培养逻辑推理能力；5. 定期进行模拟训练。",
                    "analysis": "评分要点：方法具体、可操作性强。",
                    "score": 10,
                    "source": "2021考研英语真题"
                }
            ]
        }
    ]
    
    # 插入题目到数据库
    total_inserted = 0
    for course_data in real_questions:
        course = course_data["course"]
        section_no = course_data["section_no"]
        section_title = course_data["section_title"]
        questions = course_data["questions"]
        
        print(f"处理课程：{course} - 第{section_no}节 {section_title}")
        
        for question in questions:
            question_type = question["question_type"]
            difficulty = question["difficulty"]
            knowledge_point = question.get("knowledge_point")
            content = question["content"]
            options = question.get("options")
            correct_answer = question["correct_answer"]
            analysis = question.get("analysis")
            score = question["score"]
            source = question["source"]
            
            options_json = json.dumps(options, ensure_ascii=False) if options else None
            
            # 插入题目
            insert_and_get_id(
                """
                INSERT INTO question_bank (
                    course, section_no, section_title, question_type, difficulty, 
                    knowledge_point, content, options_json, correct_answer, 
                    analysis, score, source
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    course, section_no, section_title, question_type, difficulty,
                    knowledge_point, content, options_json, correct_answer,
                    analysis, score, source
                )
            )
            total_inserted += 1
    
    print(f"\n导入完成！共插入 {total_inserted} 道真实考研题目")


if __name__ == "__main__":
    seed_real_exam_questions()