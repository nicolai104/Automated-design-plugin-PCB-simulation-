from typing import Dict, Any, List


class NetlistConverter:
    def __init__(self):
        self.spice_format = "spice"
        self.edif_format = "edif"
        self.json_format = "json"

    def convert(
        self,
        netlist_data: Dict[str, Any],
        target_format: str
    ) -> str:
        if target_format == self.spice_format:
            return self.to_spice(netlist_data)
        elif target_format == self.edif_format:
            return self.to_edif(netlist_data)
        elif target_format == self.json_format:
            return self.to_json(netlist_data)
        else:
            raise ValueError(f"Unsupported target format: {target_format}")

    def to_spice(self, netlist_data: Dict[str, Any]) -> str:
        lines = []

        title = netlist_data.get("title", "Converted Netlist")
        lines.append(title)

        components = netlist_data.get("components", [])
        for comp in components:
            comp_type = comp.get("type", "")
            designator = comp.get("designator", "")
            nodes = comp.get("nodes", [])
            value = comp.get("value", "")

            if comp_type == "resistor":
                line = f"R{designator[1:]} {nodes[0]} {nodes[1]} {value}"
            elif comp_type == "capacitor":
                line = f"C{designator[1:]} {nodes[0]} {nodes[1]} {value}"
            elif comp_type == "inductor":
                line = f"L{designator[1:]} {nodes[0]} {nodes[1]} {value}"
            elif comp_type == "voltage_source":
                line = f"V{designator[1:]} {nodes[0]} {nodes[1]} {value}"
            elif comp_type == "current_source":
                line = f"I{designator[1:]} {nodes[0]} {nodes[1]} {value}"
            else:
                line = f"X{designator[1:]} {' '.join(nodes)} {value}"

            lines.append(line)

        nets = netlist_data.get("nets", {})
        for net_name, net_nodes in nets.items():
            for node in net_nodes:
                if isinstance(node, dict):
                    component = node.get("component", "")
                    pin = node.get("pin", "")
                    lines.append(f"{net_name} {component} {pin}")

        lines.append(".end")

        return "\n".join(lines)

    def to_edif(self, netlist_data: Dict[str, Any]) -> str:
        import json
        edif_data = {
            "edif": "2 0",
            "design": {
                "name": netlist_data.get("title", "PCB Design"),
                "status": "draft"
            },
            "components": [],
            "nets": []
        }

        components = netlist_data.get("components", [])
        for comp in components:
            edif_data["components"].append({
                "name": comp.get("designator", ""),
                "type": comp.get("type", ""),
                "value": comp.get("value", "")
            })

        nets = netlist_data.get("nets", {})
        for net_name, net_nodes in nets.items():
            edif_data["nets"].append({
                "name": net_name,
                "nodes": net_nodes
            })

        return json.dumps(edif_data, indent=2)

    def to_json(self, netlist_data: Dict[str, Any]) -> str:
        import json
        return json.dumps(netlist_data, indent=2)

    def extract_ground_nets(self, netlist_data: Dict[str, Any]) -> List[str]:
        ground_nets = []
        nets = netlist_data.get("nets", {})

        for net_name in nets.keys():
            if any(gn in net_name.upper() for gn in ["GND", "VSS", "AGND", "DGND"]):
                ground_nets.append(net_name)

        return ground_nets

    def extract_power_nets(self, netlist_data: Dict[str, Any]) -> List[str]:
        power_nets = []
        nets = netlist_data.get("nets", {})

        for net_name in nets.keys():
            if any(pn in net_name.upper() for pn in ["VCC", "VDD", "AVDD", "DVDD", "PWR"]):
                power_nets.append(net_name)

        return power_nets

    def get_signal_nets(self, netlist_data: Dict[str, Any]) -> List[str]:
        ground_nets = set(self.extract_ground_nets(netlist_data))
        power_nets = set(self.extract_power_nets(netlist_data))
        all_nets = set(netlist_data.get("nets", {}).keys())

        signal_nets = all_nets - ground_nets - power_nets

        return list(signal_nets)
