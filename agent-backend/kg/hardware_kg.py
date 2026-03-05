from typing import List, Dict, Any


class HardwareKnowledgeGraph:
    def __init__(self):
        self.components_db = self._init_components_db()
        self.rules = self._init_rules()

    def _init_components_db(self) -> Dict[str, Any]:
        return {
            "IC": {
                "category": "集成电路",
                "placement_rules": ["靠近相关器件", "电源引脚就近滤波电容"],
                "priority": "high"
            },
            "R": {
                "category": "电阻",
                "placement_rules": ["根据信号流向布置", "精密电阻远离热源"],
                "priority": "medium"
            },
            "C": {
                "category": "电容",
                "placement_rules": ["靠近电源引脚", "退耦电容尽量靠近IC电源引脚"],
                "priority": "high"
            },
            "L": {
                "category": "电感",
                "placement_rules": ["远离敏感信号", "注意磁场干扰"],
                "priority": "medium"
            },
            "U": {
                "category": "芯片",
                "placement_rules": ["考虑散热", "均匀分布热量"],
                "priority": "high"
            }
        }

    def _init_rules(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "电源完整性",
                "description": "电源引脚应就近放置退耦电容",
                "severity": "high"
            },
            {
                "name": "信号完整性",
                "description": "高速信号线应尽量短且直",
                "severity": "high"
            },
            {
                "name": "热管理",
                "description": "发热器件应均匀分布，避免集中",
                "severity": "medium"
            },
            {
                "name": "模拟数字分离",
                "description": "模拟地和数字地应单点连接",
                "severity": "medium"
            }
        ]

    def analyze_circuit(
        self,
        components: List[Dict[str, Any]],
        nets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        analysis = {
            "component_count": len(components),
            "net_count": len(nets),
            "categories": self._count_categories(components),
            "potential_issues": self._identify_issues(components, nets),
            "recommendations": self._generate_recommendations(components, nets)
        }

        return analysis

    def _count_categories(self, components: List[Dict[str, Any]]) -> Dict[str, int]:
        categories = {}
        for comp in components:
            name = comp.get("name", "")
            footprint = comp.get("footprint", "")

            if "IC" in name.upper() or "U" in str(comp.get("designator", "")):
                categories["IC"] = categories.get("IC", 0) + 1
            elif "R" in str(comp.get("designator", "")):
                categories["电阻"] = categories.get("电阻", 0) + 1
            elif "C" in str(comp.get("designator", "")):
                categories["电容"] = categories.get("电容", 0) + 1
            elif "L" in str(comp.get("designator", "")):
                categories["电感"] = categories.get("电感", 0) + 1

        return categories

    def _identify_issues(
        self,
        components: List[Dict[str, Any]],
        nets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        issues = []

        power_nets = [n for n in nets if self._is_power_net(n.get("name", ""))]
        signal_nets = [n for n in nets if not self._is_power_net(n.get("name", ""))]

        if len(power_nets) == 0:
            issues.append({
                "type": "缺少电源网络",
                "severity": "high",
                "description": "未检测到电源网络，请检查原理图"
            })

        if len(components) > 100:
            issues.append({
                "type": "元器件数量过多",
                "severity": "medium",
                "description": f"检测到{len(components)}个元器件，建议分模块设计"
            })

        return issues

    def _is_power_net(self, net_name: str) -> bool:
        power_nets = ["VCC", "VDD", "GND", "VSS", "AVDD", "DVDD"]
        net_upper = net_name.upper()
        return any(power in net_upper for power in power_nets)

    def _generate_recommendations(
        self,
        components: List[Dict[str, Any]],
        nets: List[Dict[str, Any]]
    ) -> List[str]:
        recommendations = []

        recommendations.append("1. 布局时应遵循先整体后局部的原则")
        recommendations.append("2. 关键IC周围应预留足够的调试空间")
        recommendations.append("3. 电源部分应放置在板边便于散热")

        power_nets = [n for n in nets if self._is_power_net(n.get("name", ""))]
        if power_nets:
            recommendations.append(f"4. 检测到{len(power_nets)}个电源网络，应注意电源完整性设计")

        return recommendations

    def get_component_info(self, component_type: str) -> Dict[str, Any]:
        return self.components_db.get(component_type, {
            "category": "未知",
            "placement_rules": ["按常规布局"],
            "priority": "low"
        })

    def get_design_rules(self) -> List[Dict[str, Any]]:
        return self.rules
