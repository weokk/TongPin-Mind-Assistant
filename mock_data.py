"""
同频心智助手 Mock 数据模块
提供演示模式的预设响应数据
"""

from typing import Optional

# ============================================================
# Mock 响应数据（V1 翻译/解码）
# ============================================================

MOCK_RESPONSES = [
    # 1. 顺向翻译：整理货架
    {
        "input": "把那边整理一下",
        "mode": "forward",
        "response": {
            "type": "forward",
            "title": "📢 提词剧本",
            "script": "小王，请把地上散落的5个纸箱搬到右边的蓝色货架第二层。搬完一个告诉我。",
            "steps": ["📦 拿一个纸箱", "🚶 走到蓝色货架", "📦 放到第二层", "✅ 告诉我完成"],
            "visual_icons": ["📦", "🚶", "🟦", "✅"],
            "wait_reminder": "⏱️ 说完后请等待 5 秒，不要追问",
            "sensory_warning": None,
            "encouragement": None,
            "anchor_sentence": "把纸箱放到蓝色货架上",
            "fallback_task": None,
            "step_encouragements": None,
            "opening_encouragement": None,
            "closing_encouragement": None,
            "fatigue_warning": None,
            "timer_anchor": None,
            "dopamine_reward": None,
            "confirmation_method": None,
            "mobility_note": None,
            "rest_prompt": None,
            "fba_abc": None,
            "seat_label": None,
            "seat_reasoning": None,
            "emotional_acknowledgment": None,
            "physical_check": None,
            "aac_check": None,
            "intervention": None,
            "forbidden_responses": None,
            "insufficient_reason": None,
        }
    },
    # 2. 逆向解码：咬手指（焦虑）
    {
        "input": "他一直咬手指站在货架前不动",
        "mode": "reverse",
        "response": {
            "type": "reverse_fba",
            "title": "🔍 FBA 行为解码",
            "script": None,
            "steps": None,
            "visual_icons": None,
            "wait_reminder": None,
            "sensory_warning": None,
            "encouragement": None,
            "anchor_sentence": None,
            "fallback_task": None,
            "step_encouragements": None,
            "opening_encouragement": None,
            "closing_encouragement": None,
            "fatigue_warning": None,
            "timer_anchor": None,
            "dopamine_reward": None,
            "confirmation_method": None,
            "mobility_note": None,
            "rest_prompt": None,
            "fba_abc": {
                "antecedent": "货架前有多个纸箱需要整理，任务目标不明确",
                "behavior": "咬手指、站在原地不动",
                "consequence": "任务停滞，主管可能感到焦虑"
            },
            "seat_label": "E",
            "seat_reasoning": "员工可能因为任务不明确或不知道下一步该做什么而选择逃避。咬手指是自我安抚行为，表明内心焦虑。",
            "emotional_acknowledgment": None,
            "physical_check": None,
            "aac_check": None,
            "intervention": "不要走过去问\"你怎么了\"。请静静走到他身边，用手指指向第一个纸箱，只说\"这个\"。等待他拿起纸箱后再指向货架。",
            "forbidden_responses": ["你怎么了？", "快点！", "要帮你吗？", "别咬手指了"],
            "insufficient_reason": None,
        }
    },
    # 3. 顺向翻译：去除时间压力
    {
        "input": "动作快点，今天来不及了",
        "mode": "forward",
        "response": {
            "type": "forward",
            "title": "📢 提词剧本",
            "script": "小王，请把货架上的过期商品拿到左边的回收箱里。拿完一个告诉我。",
            "steps": ["🔍 找过期商品", "📦 拿起来", "🚶 走到回收箱", "📦 放进去", "✅ 告诉我"],
            "visual_icons": ["🔍", "📦", "🚶", "📦", "✅"],
            "wait_reminder": "⏱️ 说完后请等待 5 秒，不要追问",
            "sensory_warning": None,
            "encouragement": None,
            "anchor_sentence": "把过期商品放到回收箱",
            "fallback_task": None,
            "step_encouragements": None,
            "opening_encouragement": None,
            "closing_encouragement": None,
            "fatigue_warning": None,
            "timer_anchor": None,
            "dopamine_reward": None,
            "confirmation_method": None,
            "mobility_note": None,
            "rest_prompt": None,
            "fba_abc": None,
            "seat_label": None,
            "seat_reasoning": None,
            "emotional_acknowledgment": None,
            "physical_check": None,
            "aac_check": None,
            "intervention": None,
            "forbidden_responses": None,
            "insufficient_reason": None,
        }
    },
    # 4. 逆向解码：捂耳朵蹲下（感官超载）
    {
        "input": "他突然坐到地上捂住耳朵蹲下",
        "mode": "reverse",
        "response": {
            "type": "reverse_fba",
            "title": "🔍 FBA 行为解码",
            "script": None,
            "steps": None,
            "visual_icons": None,
            "wait_reminder": None,
            "sensory_warning": None,
            "encouragement": None,
            "anchor_sentence": None,
            "fallback_task": None,
            "step_encouragements": None,
            "opening_encouragement": None,
            "closing_encouragement": None,
            "fatigue_warning": None,
            "timer_anchor": None,
            "dopamine_reward": None,
            "confirmation_method": None,
            "mobility_note": None,
            "rest_prompt": None,
            "fba_abc": {
                "antecedent": "环境噪音突然增大（可能是广播、设备声或人群嘈杂）",
                "behavior": "坐到地上、捂住耳朵、蹲下",
                "consequence": "员工处于感官超载状态，需要立即干预"
            },
            "seat_label": "S",
            "seat_reasoning": "捂耳朵是典型的感官防御行为。员工正在经历听觉超载，需要立即降低环境刺激。",
            "emotional_acknowledgment": None,
            "physical_check": None,
            "aac_check": None,
            "intervention": "① 立即停止所有指令，不要说话。② 轻轻走到他身边，挡住噪音来源方向。③ 用手势示意他可以跟你去安静的地方。④ 带他到休息区，等待5-10分钟后再尝试简单任务。",
            "forbidden_responses": ["你怎么了？", "站起来！", "别这样", "大家都在看你"],
            "insufficient_reason": None,
        }
    },
    # 5. 顺向翻译：量化完成标准
    {
        "input": "差不多就行",
        "mode": "forward",
        "response": {
            "type": "forward",
            "title": "📢 提词剧本",
            "script": "小王，请把货架上的商品正面朝外摆放整齐。摆完这一排告诉我。",
            "steps": ["👀 看商品正面", "↔️ 转正方向", "📏 对齐边缘", "✅ 告诉我"],
            "visual_icons": ["👀", "↔️", "📏", "✅"],
            "wait_reminder": "⏱️ 说完后请等待 5 秒，不要追问",
            "sensory_warning": None,
            "encouragement": None,
            "anchor_sentence": "把商品正面朝外摆放",
            "fallback_task": None,
            "step_encouragements": None,
            "opening_encouragement": None,
            "closing_encouragement": None,
            "fatigue_warning": None,
            "timer_anchor": None,
            "dopamine_reward": None,
            "confirmation_method": None,
            "mobility_note": None,
            "rest_prompt": None,
            "fba_abc": None,
            "seat_label": None,
            "seat_reasoning": None,
            "emotional_acknowledgment": None,
            "physical_check": None,
            "aac_check": None,
            "intervention": None,
            "forbidden_responses": None,
            "insufficient_reason": None,
        }
    },
    # 6. 逆向解码：推倒货架（Attention/Escape）
    {
        "input": "他把货架上的东西全推下来了",
        "mode": "reverse",
        "response": {
            "type": "reverse_fba",
            "title": "🔍 FBA 行为解码",
            "script": None,
            "steps": None,
            "visual_icons": None,
            "wait_reminder": None,
            "sensory_warning": None,
            "encouragement": None,
            "anchor_sentence": None,
            "fallback_task": None,
            "step_encouragements": None,
            "opening_encouragement": None,
            "closing_encouragement": None,
            "fatigue_warning": None,
            "timer_anchor": None,
            "dopamine_reward": None,
            "confirmation_method": None,
            "mobility_note": None,
            "rest_prompt": None,
            "fba_abc": {
                "antecedent": "可能长时间未被关注，或任务难度超出能力范围",
                "behavior": "把货架上的东西推下来",
                "consequence": "引起注意，任务被迫中断"
            },
            "seat_label": "A",
            "seat_reasoning": "推倒物品是一种强烈的注意寻求行为。员工可能感到被忽视或任务压力过大，通过破坏性行为获取关注或逃避任务。",
            "emotional_acknowledgment": None,
            "physical_check": None,
            "aac_check": None,
            "intervention": "① 确保员工和周围人员安全。② 不要大声责备，保持平静。③ 引导员工离开现场到安静区域。④ 等待情绪平复后，用简单指令重新开始任务。⑤ 后续需要评估任务难度是否超出能力范围。",
            "forbidden_responses": ["你干什么！", "太不像话了", "怎么这么不听话", "给我捡起来"],
            "insufficient_reason": None,
        }
    },
    # 7. 逆向解码：重复说话（Attention + Escape）
    {
        "input": "他今天反复说同一句话，不听指令",
        "mode": "reverse",
        "response": {
            "type": "reverse_fba",
            "title": "🔍 FBA 行为解码",
            "script": None,
            "steps": None,
            "visual_icons": None,
            "wait_reminder": None,
            "sensory_warning": None,
            "encouragement": None,
            "anchor_sentence": None,
            "fallback_task": None,
            "step_encouragements": None,
            "opening_encouragement": None,
            "closing_encouragement": None,
            "fatigue_warning": None,
            "timer_anchor": None,
            "dopamine_reward": None,
            "confirmation_method": None,
            "mobility_note": None,
            "rest_prompt": None,
            "fba_abc": {
                "antecedent": "当前任务可能过于枯燥或难以理解",
                "behavior": "反复说同一句话，不响应指令",
                "consequence": "任务无法继续，获得注意"
            },
            "seat_label": "E",
            "seat_reasoning": "重复语言可能是自我刺激行为，也可能是逃避困难任务的方式。需要判断重复的内容是否有意义。",
            "emotional_acknowledgment": None,
            "physical_check": None,
            "aac_check": None,
            "intervention": "① 不要打断或纠正他的重复语言。② 等待他停顿的间隙，用简单指令引导：\"先做这个\"（指向具体物品）。③ 如果任务确实困难，降低难度或回到已掌握的任务。",
            "forbidden_responses": ["别说了！", "听我说！", "你能不能安静点", "再这样我就走了"],
            "insufficient_reason": None,
        }
    },
    # 8. 信息不足提示
    {
        "input": "帮我搞定那个事",
        "mode": "forward",
        "response": {
            "type": "insufficient_info",
            "title": "⚠️ 信息不足",
            "script": None,
            "steps": None,
            "visual_icons": None,
            "wait_reminder": None,
            "sensory_warning": None,
            "encouragement": None,
            "anchor_sentence": None,
            "fallback_task": None,
            "step_encouragements": None,
            "opening_encouragement": None,
            "closing_encouragement": None,
            "fatigue_warning": None,
            "timer_anchor": None,
            "dopamine_reward": None,
            "confirmation_method": None,
            "mobility_note": None,
            "rest_prompt": None,
            "fba_abc": None,
            "seat_label": None,
            "seat_reasoning": None,
            "emotional_acknowledgment": None,
            "physical_check": None,
            "aac_check": None,
            "intervention": None,
            "forbidden_responses": None,
            "insufficient_reason": "指令中缺少以下关键信息：\n• 具体是什么任务？\n• 涉及哪些物品？\n• 需要做什么操作？\n\n请补充具体信息后重新输入。",
        }
    },
]


def find_mock_response(user_input: str, mode: str) -> Optional[dict]:
    """
    查找匹配的 Mock 响应

    Args:
        user_input: 用户输入文本
        mode: "forward" 或 "reverse"

    Returns:
        匹配的响应数据，如果没有匹配则返回 None
    """
    # 标准化输入
    normalized_input = user_input.strip().lower()

    for item in MOCK_RESPONSES:
        if item["mode"] == mode:
            # 检查是否包含关键词
            mock_input = item["input"].lower()

            # 精确匹配
            if normalized_input == mock_input:
                return item["response"]

            # 关键词匹配
            keywords = mock_input.split()
            if any(kw in normalized_input for kw in keywords if len(kw) > 2):
                return item["response"]

    # 如果没有匹配，返回默认响应
    return None


def get_default_mock_response(mode: str) -> dict:
    """
    获取默认 Mock 响应（当没有匹配时使用）

    Args:
        mode: "forward" 或 "reverse"

    Returns:
        默认响应数据
    """
    if mode == "forward":
        return {
            "type": "forward",
            "title": "📢 提词剧本",
            "script": "小王，请完成这个任务。做完告诉我。",
            "steps": ["📋 看清任务", "✋ 开始操作", "✅ 完成后告诉我"],
            "visual_icons": ["📋", "✋", "✅"],
            "wait_reminder": "⏱️ 说完后请等待 5 秒，不要追问",
            "sensory_warning": None,
            "encouragement": None,
            "anchor_sentence": None,
            "fallback_task": None,
            "step_encouragements": None,
            "opening_encouragement": None,
            "closing_encouragement": None,
            "fatigue_warning": None,
            "timer_anchor": None,
            "dopamine_reward": None,
            "confirmation_method": None,
            "mobility_note": None,
            "rest_prompt": None,
            "fba_abc": None,
            "seat_label": None,
            "seat_reasoning": None,
            "emotional_acknowledgment": None,
            "physical_check": None,
            "aac_check": None,
            "intervention": None,
            "forbidden_responses": None,
            "insufficient_reason": None,
        }
    else:
        return {
            "type": "reverse_fba",
            "title": "🔍 FBA 行为解码",
            "script": None,
            "steps": None,
            "visual_icons": None,
            "wait_reminder": None,
            "sensory_warning": None,
            "encouragement": None,
            "anchor_sentence": None,
            "fallback_task": None,
            "step_encouragements": None,
            "opening_encouragement": None,
            "closing_encouragement": None,
            "fatigue_warning": None,
            "timer_anchor": None,
            "dopamine_reward": None,
            "confirmation_method": None,
            "mobility_note": None,
            "rest_prompt": None,
            "fba_abc": {
                "antecedent": "需要更多信息来确定前因",
                "behavior": "员工表现出异常行为",
                "consequence": "任务受到影响"
            },
            "seat_label": "E",
            "seat_reasoning": "根据描述，员工可能因任务困难或环境因素而选择逃避。建议观察具体触发因素。",
            "emotional_acknowledgment": None,
            "physical_check": None,
            "aac_check": None,
            "intervention": "① 保持平静，不要追问。② 观察环境是否有明显触发因素。③ 尝试用简单指令引导回到任务。",
            "forbidden_responses": ["你怎么了？", "快点！", "别这样"],
            "insufficient_reason": None,
        }


# ============================================================
# 任务分解 Mock 数据
# ============================================================

MOCK_TASK_SEQUENCE = {
    "input": "今天负责饮料区上货和整理",
    "mode": "decompose",
    "response": [
        {
            "id": 1,
            "duration_min": 20,
            "script": "请把饮料区地上的纸箱搬到蓝色货架第二层。搬完一个告诉我。",
            "steps": ["拿纸箱", "走到货架", "放上去"],
            "visual_icons": ["📦", "🚶", "🟦"],
            "confirmation": "举手或点头",
            "is_break": False
        },
        {
            "id": 2,
            "duration_min": 20,
            "script": "请检查饮料保质期，把过期饮料拿出来放到回收箱。",
            "steps": ["看日期", "拿过期饮料", "放回收箱"],
            "visual_icons": ["🔍", "📦", "♻️"],
            "confirmation": "举手或点头",
            "is_break": False
        },
        {
            "id": 3,
            "duration_min": 10,
            "script": "休息一下，可以喝点水。休息结束后告诉我。",
            "steps": ["休息"],
            "visual_icons": ["💧"],
            "confirmation": None,
            "is_break": True
        },
        {
            "id": 4,
            "duration_min": 20,
            "script": "请把新到的饮料按类别摆放到货架上。摆完一排告诉我。",
            "steps": ["看类别", "摆放到货架", "对齐标签"],
            "visual_icons": ["👀", "📦", "🏷️"],
            "confirmation": "举手或点头",
            "is_break": False
        },
        {
            "id": 5,
            "duration_min": 10,
            "script": "请整理饮料区地面，把空纸箱叠放整齐。做完告诉我。",
            "steps": ["收空纸箱", "叠放整齐"],
            "visual_icons": ["📦", "📦"],
            "confirmation": "举手或点头",
            "is_break": False
        },
        {
            "id": 6,
            "duration_min": 10,
            "script": "休息一下，可以走动走动。休息结束后告诉我。",
            "steps": ["休息"],
            "visual_icons": ["💧"],
            "confirmation": None,
            "is_break": True
        },
        {
            "id": 7,
            "duration_min": 20,
            "script": "请检查货架上的价签是否对齐。不对齐的告诉我。",
            "steps": ["看价签", "对齐价签"],
            "visual_icons": ["🏷️", "✏️"],
            "confirmation": "举手或点头",
            "is_break": False
        },
        {
            "id": 8,
            "duration_min": 10,
            "script": "今天的工作完成了，做得很好！请整理工具并告诉主管。",
            "steps": ["整理工具", "告诉主管"],
            "visual_icons": ["🧹", "✅"],
            "confirmation": "举手或点头",
            "is_break": False
        }
    ]
}


def find_mock_task_sequence(user_input: str) -> Optional[list]:
    """
    查找匹配的任务分解 Mock 响应

    Args:
        user_input: 用户输入的任务描述

    Returns:
        匹配的任务序列列表，如果没有匹配则返回 None
    """
    normalized_input = user_input.strip().lower()
    # 关键词匹配：包含"饮料"或"上货"或"整理"返回预设数据
    keywords = ["饮料", "上货", "整理"]
    if any(kw in normalized_input for kw in keywords):
        return MOCK_TASK_SEQUENCE["response"]
    return None


def get_default_mock_task_sequence(duration_min: int = 120) -> list:
    """
    获取默认的任务分解 Mock 响应（根据时长动态生成）

    Args:
        duration_min: 工作时长（分钟）

    Returns:
        通用任务序列列表
    """
    # 根据时长计算任务数量（每个任务约 20 分钟，每 60 分钟插入一个休息）
    tasks = []
    task_id = 1
    remaining = duration_min
    work_cycle = 0

    while remaining > 0:
        work_cycle += 1
        # 工作任务
        task_duration = min(20, remaining)
        tasks.append({
            "id": task_id,
            "duration_min": task_duration,
            "script": f"请完成当前分配的工作任务。做完告诉我。",
            "steps": ["看清任务", "开始操作", "完成后确认"],
            "visual_icons": ["📋", "✋", "✅"],
            "confirmation": "举手或点头",
            "is_break": False
        })
        task_id += 1
        remaining -= task_duration

        # 每完成 2 个工作任务插入一个休息
        if work_cycle % 2 == 0 and remaining > 0:
            break_duration = min(10, remaining)
            tasks.append({
                "id": task_id,
                "duration_min": break_duration,
                "script": "休息一下，可以喝点水。休息结束后告诉我。",
                "steps": ["休息"],
                "visual_icons": ["💧"],
                "confirmation": None,
                "is_break": True
            })
            task_id += 1
            remaining -= break_duration

    # 添加收尾任务
    tasks.append({
        "id": task_id,
        "duration_min": 10,
        "script": "今天的工作完成了，做得很好！请整理工具并告诉主管。",
        "steps": ["整理工具", "告诉主管"],
        "visual_icons": ["🧹", "✅"],
        "confirmation": "举手或点头",
        "is_break": False
    })

    return tasks


# ============================================================
# 岗位适配评估 Mock 数据
# ============================================================

MOCK_JOB_FIT_REPORT = {
    "input": "超市理货员",
    "mode": "job_fit",
    "response": {
        "scores": {
            "cognitive": {"score": 82, "reasoning": "员工工作记忆2步，岗位主要任务为单步操作，认知负荷匹配度较高。部分复杂任务（如多区域协调）可能超出能力范围。"},
            "sensory": {"score": 55, "reasoning": "超市环境噪音中等偏高，员工对突然大声敏感。冷柜区域温度变化和 fluorescent 灯光可能构成额外感官刺激。"},
            "social": {"score": 88, "reasoning": "岗位无需与顾客直接沟通，社交要求低。偶尔需要与同事交接，但频率低且内容固定。"},
            "structure": {"score": 72, "reasoning": "理货任务有一定规律性，但需跨区域流动。每日任务顺序可能因到货情况变化，结构化程度中等。"}
        },
        "risk_items": [
            {
                "description": "超市广播和背景音乐可能触发感官超载",
                "level": "high",
                "support": "申请为员工配备降噪耳塞，或将工位调整到远离广播的区域"
            },
            {
                "description": "促销活动期间人流密集可能引发焦虑",
                "level": "medium",
                "support": "促销期间安排员工在仓库区域工作，避免直接面对密集人流"
            },
            {
                "description": "冷柜区域温度变化可能造成身体不适",
                "level": "medium",
                "support": "避免安排冷柜区域长时间工作，每次不超过20分钟"
            }
        ],
        "onboarding_plan": {
            "week1": [
                "辅导员全程陪岗，仅安排单一货架区域的整理任务",
                "每天工作2小时，从最简单的商品摆放开始",
                "建立固定的上下班仪式感：到岗→看任务卡→开始工作→完成确认→下班"
            ],
            "month1": [
                "第二周开始引入第二个货架区域，逐步扩大工作范围",
                "第三周开始学习保质期检查和价签整理",
                "第四周逐步减少陪岗时间到半天，观察独立工作能力"
            ],
            "stable": [
                "每月进行一次能力复查，更新员工画像",
                "建立紧急联系人机制：员工出现异常行为时第一时间联系辅导员",
                "每季度评估是否可以引入新的任务类型"
            ]
        },
        "job_adjustments": [
            "固定1-2个货架区域作为主要工作范围，避免频繁跨区域流动",
            "配备降噪耳塞作为标准防护用品",
            "促销期间调整工作任务为仓库内部分拣"
        ]
    }
}


def find_mock_job_fit_report(user_input: str) -> Optional[dict]:
    """
    查找匹配的岗位适配评估 Mock 响应

    Args:
        user_input: 用户输入的岗位描述

    Returns:
        匹配的评估报告字典，如果没有匹配则返回 None
    """
    normalized_input = user_input.strip().lower()
    # 关键词匹配：包含"理货"或"超市"或"便利店"返回预设数据
    keywords = ["理货", "超市", "便利店"]
    if any(kw in normalized_input for kw in keywords):
        return MOCK_JOB_FIT_REPORT["response"]
    return None


def get_default_mock_job_fit_report() -> dict:
    """
    获取默认的岗位适配评估 Mock 响应

    Returns:
        默认的评估报告字典
    """
    return {
        "scores": {
            "cognitive": {"score": 0, "reasoning": "暂无具体岗位信息，无法进行认知匹配度评估。请提供岗位名称和具体工作内容。"},
            "sensory": {"score": 0, "reasoning": "暂无具体岗位信息，无法进行感官环境评估。请提供岗位名称和工作环境描述。"},
            "social": {"score": 0, "reasoning": "暂无具体岗位信息，无法进行社交要求评估。请提供岗位名称和社交场景描述。"},
            "structure": {"score": 0, "reasoning": "暂无具体岗位信息，无法进行结构化程度评估。请提供岗位名称和日常工作流程描述。"}
        },
        "risk_items": [
            {
                "description": "需要更多岗位信息才能进行风险评估",
                "level": "low",
                "support": "请提供具体的岗位名称、工作内容和工作环境信息"
            }
        ],
        "onboarding_plan": {
            "week1": [
                "需要更多岗位信息才能制定入职计划",
                "请提供具体的岗位名称和工作内容"
            ],
            "month1": [],
            "stable": []
        },
        "job_adjustments": [
            "需要更多岗位信息才能提出合理的岗位调整建议"
        ]
    }
