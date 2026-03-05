from typing import List, Dict, Any, Optional


class PromptTemplate:
    SYSTEM_PROMPT = """你是一位专业的PCB设计助手，专门帮助用户进行电路设计、布局和仿真。
    
你可以帮助用户：
1. PCB布局优化 - 根据元器件连接关系和信号类型优化元器件位置
2. 电路仿真 - 配置和运行DC、AC、瞬态仿真
3. 电路分析 - 分析原理图连接关系，识别潜在问题
4. 设计建议 - 提供PCB设计最佳实践和建议

请用中文回答问题，并尽可能提供专业的技术建议。"""

    @staticmethod
    def build_chat_prompt(
        message: str,
        context: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        prompt = f"{PromptTemplate.SYSTEM_PROMPT}\n\n"

        if history:
            prompt += "对话历史：\n"
            for msg in history[-10:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt += f"{role}: {content}\n"

        prompt += f"\n当前问题：{message}\n"

        if context:
            components = context.get("components", [])
            nets = context.get("nets", [])
            if components:
                prompt += f"\n当前设计包含 {len(components)} 个元器件"
            if nets:
                prompt += f"，{len(nets)} 个网络"

        prompt += "\n请给出专业的建议和帮助。"

        return prompt

    @staticmethod
    def build_layout_prompt(
        components: List[Dict[str, Any]],
        nets: List[Dict[str, Any]],
        constraints: List[Dict[str, Any]]
    ) -> str:
        prompt = f"""请为以下PCB设计生成优化的元器件布局。

元器件清单：
"""

        for comp in components:
            prompt += f"- {comp.get('designator', 'Unknown')}: {comp.get('name', 'Unknown')} "
            prompt += f"(封装: {comp.get('footprint', 'Unknown')})\n"

        prompt += f"\n网络连接：\n"
        for net in nets:
            nodes = net.get("nodes", [])
            prompt += f"- {net.get('name', 'NET')}: "
            prompt += ", ".join([f"{n.get('componentId','')}.{n.get('pinNumber','')}" for n in nodes])
            prompt += "\n"

        if constraints:
            prompt += f"\n布局约束：\n"
            for constraint in constraints:
                prompt += f"- {constraint.get('type', 'unknown')}: "
                prompt += f"({constraint.get('x', 0)}, {constraint.get('y', 0)}) "
                prompt += f"尺寸: {constraint.get('width', 0)}x{constraint.get('height', 0)}\n"

        prompt += """
请以JSON格式返回布局结果，格式如下：
{
    "components": [
        {"id": "元器件ID", "x": x坐标, "y": y坐标, "rotation": 旋转角度}
    ],
    "warnings": ["警告信息列表"]
}

请只返回JSON，不要包含其他内容。"""

        return prompt

    @staticmethod
    def build_simulation_prompt(
        netlist: Dict[str, Any],
        config: Dict[str, Any]
    ) -> str:
        sim_type = config.get("type", "Transient")
        params = config.get("parameters", {})

        prompt = f"""请为以下电路配置仿真参数并执行仿真。

仿真类型：{sim_type}
仿真参数：{json.dumps(params, ensure_ascii=False)}

网表信息：
{json.dumps(netlist, ensure_ascii=False, indent=2)}

请以JSON格式返回仿真结果，格式如下：
{{
    "type": "{sim_type}",
    "data": [仿真数据数组],
    "time": [时间轴数据] (仅瞬态仿真需要),
    "frequency": [频率轴数据] (仅AC仿真需要),
    "success": true/false,
    "message": "结果描述"
}}

请只返回JSON，不要包含其他内容。"""

        return prompt

    @staticmethod
    def build_analysis_prompt(
        components: List[Dict[str, Any]],
        nets: List[Dict[str, Any]],
        kg_analysis: Dict[str, Any]
    ) -> str:
        prompt = f"""请分析以下电路设计并提供专业建议。

元器件统计：
- 总数：{len(components)}
- 详细：{json.dumps(components, ensure_ascii=False, indent=2)}

网络统计：
- 总数：{len(nets)}
- 详细：{json.dumps(nets, ensure_ascii=False, indent=2)}

知识图谱分析结果：
{json.dumps(kg_analysis, ensure_ascii=False, indent=2)}

请提供：
1. 电路整体评估
2. 潜在问题和建议
3. 布局优化建议（如果适用）
4. 仿真需求建议

请用中文回答。"""

        return prompt
