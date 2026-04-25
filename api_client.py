"""
同频心智助手 API 客户端模块
处理与 OpenAI 兼容 API 的通信
"""

import json
import requests
from typing import Optional, Tuple
from data_manager import DataManager
from prompts import build_system_prompt, build_user_message

# ============================================================
# API 客户端类
# ============================================================

class APIClient:
    """OpenAI 兼容 API 客户端"""

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    def _get_headers(self) -> dict:
        """获取请求头"""
        api_key = self.data_manager.get_api_key()
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def _get_endpoint(self) -> str:
        """获取 API 端点"""
        base_url = self.data_manager.get_api_base_url().rstrip("/")
        return f"{base_url}/chat/completions"

    def test_connection(self) -> Tuple[bool, str]:
        """
        测试 API 连接

        Returns:
            (success, message)
        """
        api_key = self.data_manager.get_api_key()
        if not api_key:
            return False, "API Key 未配置"

        try:
            response = requests.post(
                self._get_endpoint(),
                headers=self._get_headers(),
                json={
                    "model": self.data_manager.get_model(),
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10,
                },
                timeout=10,
            )

            if response.status_code == 200:
                return True, "API 连接成功"
            elif response.status_code == 401:
                return False, "API Key 无效"
            elif response.status_code == 429:
                return False, "请求过于频繁，请稍后重试"
            else:
                return False, f"API 错误: {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "连接超时，请检查网络"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到 API 服务器"
        except Exception as e:
            return False, f"连接失败: {str(e)}"

    def test_connection_with_config(self, base_url: str, api_key: str, model: str) -> Tuple[bool, str]:
        """使用指定配置测试 API 连接（不依赖已保存的配置）"""
        if not api_key:
            return False, "请先输入 API Key"
        try:
            endpoint = f"{base_url.rstrip('/')}/chat/completions"
            response = requests.post(
                endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 10,
                },
                timeout=10,
            )
            if response.status_code == 200:
                return True, f"连接成功！模型：{model}"
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text[:200])
                except Exception:
                    error_msg = response.text[:200]
                return False, f"连接失败（HTTP {response.status_code}）：{error_msg}"
        except requests.exceptions.Timeout:
            return False, "连接超时，请检查网络或 API 地址"
        except requests.exceptions.ConnectionError:
            return False, "无法连接，请检查 API 地址是否正确"
        except Exception as e:
            return False, f"连接异常：{str(e)}"

    def translate(
        self,
        employee: dict,
        user_input: str,
        mode: str,
        context_messages: list = None,
    ) -> Tuple[Optional[dict], str]:
        """
        调用 API 进行翻译

        Args:
            employee: 员工画像
            user_input: 用户输入文本
            mode: "forward" 或 "reverse"
            context_messages: 对话上下文

        Returns:
            (result, error_message)
            result 为 None 表示失败，error_message 包含错误信息
        """
        api_key = self.data_manager.get_api_key()
        if not api_key:
            return None, "API Key 未配置，请先在设置中配置 API Key"

        # 构建 System Prompt
        system_prompt = build_system_prompt(employee)

        # 构建用户消息
        user_message = build_user_message(user_input, mode)

        # 构建消息列表
        messages = [{"role": "system", "content": system_prompt}]

        # 添加上下文
        if context_messages:
            messages.extend(context_messages)

        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})

        model = self.data_manager.get_model()

        def _do_request(use_response_format: bool):
            """执行 API 请求"""
            payload = {
                "model": model,
                "messages": messages,
                "temperature": 0.3,  # 较低的温度以保证一致性
                "max_tokens": 2000,
            }
            if use_response_format:
                payload["response_format"] = {"type": "json_object"}
            return requests.post(
                self._get_endpoint(),
                headers=self._get_headers(),
                json=payload,
                timeout=30,
            )

        try:
            # 第一次尝试：带 response_format
            response = _do_request(use_response_format=True)

            # 如果 400 错误且与 response_format 相关，重试不带该参数
            if response.status_code == 400:
                try:
                    error_body = response.json()
                    error_msg = error_body.get("error", {}).get("message", "")
                except Exception:
                    error_msg = ""
                if "response_format" in error_msg:
                    response = _do_request(use_response_format=False)

            if response.status_code != 200:
                try:
                    error_detail = response.json().get("error", {}).get("message", "")
                except Exception:
                    error_detail = ""
                return None, f"API 错误 ({response.status_code}): {error_detail}"

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # 使用容错解析
            card_data = parse_ai_response(content)
            return card_data, ""

        except requests.exceptions.Timeout:
            return None, "请求超时，请稍后重试"
        except requests.exceptions.ConnectionError:
            return None, "网络连接失败，请检查网络设置"
        except Exception as e:
            return None, f"请求失败: {str(e)}"

    def decompose_task(self, employee: dict, task_description: str,
                       duration_min: int, include_break: bool,
                       system_prompt: str) -> Tuple[Optional[list], str]:
        """
        调用 API 进行任务分解

        Args:
            employee: 员工画像
            task_description: 任务描述
            duration_min: 工作时长（分钟）
            include_break: 是否包含休息
            system_prompt: 系统提示词（由 prompts.build_decompose_prompt 生成）

        Returns:
            (task_list, error_message)
            task_list 为 None 表示失败
        """
        api_key = self.data_manager.get_api_key()
        if not api_key:
            return None, "API Key 未配置，请先在设置中配置 API Key"

        user_message = (
            f"[任务分解] 今日任务：{task_description}\n"
            f"工作时长：{duration_min}分钟\n"
            f"是否含休息：{'是' if include_break else '否'}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        model = self.data_manager.get_model()

        try:
            response = requests.post(
                self._get_endpoint(),
                headers=self._get_headers(),
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 4096,
                },
                timeout=60,
            )

            if response.status_code != 200:
                try:
                    error_detail = response.json().get("error", {}).get("message", "")
                except Exception:
                    error_detail = ""
                return None, f"API 错误 ({response.status_code}): {error_detail}"

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # 使用任务序列解析
            task_list = parse_task_sequence(content)
            return task_list, ""

        except requests.exceptions.Timeout:
            return None, "请求超时，请稍后重试"
        except requests.exceptions.ConnectionError:
            return None, "网络连接失败，请检查网络设置"
        except Exception as e:
            return None, f"请求失败: {str(e)}"

    def assess_job_fit(self, system_prompt: str,
                       user_message: str) -> Tuple[Optional[dict], str]:
        """
        调用 API 进行岗位适配评估

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息

        Returns:
            (report, error_message)
            report 为 None 表示失败
        """
        api_key = self.data_manager.get_api_key()
        if not api_key:
            return None, "API Key 未配置，请先在设置中配置 API Key"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        model = self.data_manager.get_model()

        try:
            response = requests.post(
                self._get_endpoint(),
                headers=self._get_headers(),
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 4096,
                },
                timeout=60,
            )

            if response.status_code != 200:
                try:
                    error_detail = response.json().get("error", {}).get("message", "")
                except Exception:
                    error_detail = ""
                return None, f"API 错误 ({response.status_code}): {error_detail}"

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # 使用岗位适配评估解析
            report = parse_job_fit_report(content)
            return report, ""

        except requests.exceptions.Timeout:
            return None, "请求超时，请稍后重试"
        except requests.exceptions.ConnectionError:
            return None, "网络连接失败，请检查网络设置"
        except Exception as e:
            return None, f"请求失败: {str(e)}"


# ============================================================
# JSON 解析容错函数
# ============================================================

def parse_ai_response(raw_text: str) -> dict:
    """解析 AI 返回的 JSON，包含基础容错"""
    clean = raw_text.strip()
    # 剥离 markdown 代码块标记
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        # 一次重试：提取第一个 { } 块
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(clean[start:end])
        # 彻底失败：返回 insufficient_info 降级卡
        return {
            "type": "insufficient_info",
            "title": "⚠️ 解析失败",
            "insufficient_reason": "AI 返回格式异常，请重试",
        }


def safe_get(data: dict, key: str, default=None):
    """
    安全获取字典值，处理 None 和缺失的情况

    Args:
        data: 字典数据
        key: 键名
        default: 默认值

    Returns:
        值或默认值
    """
    if data is None:
        return default
    value = data.get(key)
    return value if value is not None else default


def parse_card_data(data: dict) -> dict:
    """
    解析并验证卡片数据，确保所有字段都存在

    Args:
        data: 原始 API 返回的 JSON 数据

    Returns:
        规范化后的卡片数据
    """
    # 定义所有可能的字段及其默认值
    fields = {
        "type": "forward",
        "title": "",
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
        "insufficient_reason": None,
    }

    result = {}
    for key, default in fields.items():
        result[key] = safe_get(data, key, default)

    return result


# ============================================================
# 任务分解与岗位适配评估解析函数
# ============================================================

def parse_task_sequence(raw_text: str) -> list:
    """解析任务分解的 JSON 数组响应"""
    clean = raw_text.strip()
    # 1. strip markdown 代码块
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        data = json.loads(clean)
        if isinstance(data, list):
            return _normalize_task_list(data)
    except json.JSONDecodeError:
        pass
    # 3. 如果失败，提取 [ ] 块
    start = clean.find("[")
    end = clean.rfind("]") + 1
    if start != -1 and end > start:
        try:
            data = json.loads(clean[start:end])
            if isinstance(data, list):
                return _normalize_task_list(data)
        except json.JSONDecodeError:
            pass
    # 4. 如果还失败，返回空列表
    return []


def _normalize_task_list(task_list: list) -> list:
    """规范化任务列表，确保每个元素都有完整字段"""
    normalized = []
    for i, task in enumerate(task_list):
        if not isinstance(task, dict):
            continue
        normalized.append({
            "id": task.get("id", i + 1),
            "duration_min": task.get("duration_min", 10),
            "script": task.get("script", ""),
            "steps": task.get("steps", []),
            "visual_icons": task.get("visual_icons", []),
            "confirmation": task.get("confirmation", None),
            "is_break": task.get("is_break", False),
        })
    return normalized


def parse_job_fit_report(raw_text: str) -> dict:
    """解析岗位适配评估的 JSON 响应"""
    clean = raw_text.strip()
    # 1. strip markdown 代码块
    if clean.startswith("```"):
        clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        data = json.loads(clean)
        if isinstance(data, dict):
            return _normalize_job_fit_report(data)
    except json.JSONDecodeError:
        pass
    # 3. 如果失败，提取 { } 块
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start != -1 and end > start:
        try:
            data = json.loads(clean[start:end])
            if isinstance(data, dict):
                return _normalize_job_fit_report(data)
        except json.JSONDecodeError:
            pass
    # 4. 如果还失败，返回降级报告
    return _get_fallback_job_fit_report()


def _normalize_job_fit_report(data: dict) -> dict:
    """规范化岗位适配评估报告，确保包含所有必要字段"""
    # 确保 scores 字段完整
    scores = data.get("scores", {})
    if not isinstance(scores, dict):
        scores = {}
    for dimension in ("cognitive", "sensory", "social", "structure"):
        if dimension not in scores or not isinstance(scores[dimension], dict):
            scores[dimension] = {"score": 0, "reasoning": "数据缺失"}
        else:
            scores[dimension].setdefault("score", 0)
            scores[dimension].setdefault("reasoning", "")

    # 确保 risk_items 字段完整
    risk_items = data.get("risk_items", [])
    if not isinstance(risk_items, list):
        risk_items = []
    for item in risk_items:
        if isinstance(item, dict):
            item.setdefault("description", "")
            item.setdefault("level", "low")
            item.setdefault("support", "")

    # 确保 onboarding_plan 字段完整
    onboarding_plan = data.get("onboarding_plan", {})
    if not isinstance(onboarding_plan, dict):
        onboarding_plan = {}
    for phase in ("week1", "month1", "stable"):
        if phase not in onboarding_plan or not isinstance(onboarding_plan[phase], list):
            onboarding_plan[phase] = []

    # 确保 job_adjustments 字段完整
    job_adjustments = data.get("job_adjustments", [])
    if not isinstance(job_adjustments, list):
        job_adjustments = []

    return {
        "scores": scores,
        "risk_items": risk_items,
        "onboarding_plan": onboarding_plan,
        "job_adjustments": job_adjustments,
    }


def _get_fallback_job_fit_report() -> dict:
    """获取降级岗位适配评估报告"""
    return {
        "scores": {
            "cognitive": {"score": 0, "reasoning": "AI 返回格式异常，无法解析"},
            "sensory": {"score": 0, "reasoning": "AI 返回格式异常，无法解析"},
            "social": {"score": 0, "reasoning": "AI 返回格式异常，无法解析"},
            "structure": {"score": 0, "reasoning": "AI 返回格式异常，无法解析"},
        },
        "risk_items": [],
        "onboarding_plan": {
            "week1": [],
            "month1": [],
            "stable": [],
        },
        "job_adjustments": [],
    }


# ============================================================
# Token 成本估算
# ============================================================

def estimate_tokens(text: str) -> int:
    """
    粗略估算文本的 token 数量
    中文约 1.5 字/token，英文约 4 字符/token

    Args:
        text: 文本内容

    Returns:
        估算的 token 数量
    """
    # 简单估算：中文按字符数，英文按单词数
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    other_chars = len(text) - chinese_chars

    # 中文约 1.5 字/token，英文约 4 字符/token
    tokens = int(chinese_chars / 1.5) + int(other_chars / 4)
    return max(tokens, 1)


def estimate_cost(input_tokens: int, output_tokens: int, model: str = "gpt-4o") -> float:
    """
    估算 API 调用成本（美元）

    支持常见模型的定价映射

    Args:
        input_tokens: 输入 token 数
        output_tokens: 输出 token 数
        model: 模型名称

    Returns:
        估算成本（美元）
    """
    # 常见模型定价映射 (input_price, output_price) 单位：美元/1M tokens
    MODEL_PRICING = {
        "gpt-4o": (2.50, 10.00),
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4-turbo": (10.00, 30.00),
        "gpt-4": (30.00, 60.00),
        "gpt-3.5-turbo": (0.50, 1.50),
        "gpt-4.1": (2.00, 8.00),
        "gpt-4.1-mini": (0.40, 1.60),
        "gpt-4.1-nano": (0.10, 0.40),
        "claude-3-5-sonnet-20241022": (3.00, 15.00),
        "claude-3-5-haiku-20241022": (0.80, 4.00),
        "deepseek-chat": (0.14, 0.28),
        "deepseek-reasoner": (0.55, 2.19),
    }

    input_price, output_price = MODEL_PRICING.get(model, (2.50, 10.00))
    input_cost = input_tokens * input_price / 1_000_000
    output_cost = output_tokens * output_price / 1_000_000

    return input_cost + output_cost
