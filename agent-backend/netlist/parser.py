from typing import Dict, Any, List, Optional
import re


class NetlistParser:
    def __init__(self):
        self.supported_formats = ["spice", "edif", "json"]

    def parse(self, netlist_content: str, format_type: str = "spice") -> Dict[str, Any]:
        if format_type == "spice":
            return self.parse_spice(netlist_content)
        elif format_type == "edif":
            return self.parse_edif(netlist_content)
        elif format_type == "json":
            return self.parse_json(netlist_content)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def parse_spice(self, netlist: str) -> Dict[str, Any]:
        components = []
        nets = {}
        title = ""

        lines = netlist.strip().split("\n")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("*") or line.startswith(";"):
                continue

            if line.startswith("."):
                continue

            if not title and not line.startswith("*"):
                title = line

            parts = line.split()
            if len(parts) < 2:
                continue

            designator = parts[0]

            if designator.startswith("R"):
                if len(parts) >= 4:
                    components.append({
                        "type": "resistor",
                        "designator": designator,
                        "nodes": [parts[1], parts[2]],
                        "value": parts[3] if len(parts) > 3 else ""
                    })

            elif designator.startswith("C"):
                if len(parts) >= 4:
                    components.append({
                        "type": "capacitor",
                        "designator": designator,
                        "nodes": [parts[1], parts[2]],
                        "value": parts[3] if len(parts) > 3 else ""
                    })

            elif designator.startswith("L"):
                if len(parts) >= 4:
                    components.append({
                        "type": "inductor",
                        "designator": designator,
                        "nodes": [parts[1], parts[2]],
                        "value": parts[3] if len(parts) > 3 else ""
                    })

            elif designator.startswith("V"):
                if len(parts) >= 4:
                    components.append({
                        "type": "voltage_source",
                        "designator": designator,
                        "nodes": [parts[1], parts[2]],
                        "value": parts[3] if len(parts) > 3 else ""
                    })

            elif designator.startswith("I"):
                if len(parts) >= 4:
                    components.append({
                        "type": "current_source",
                        "designator": designator,
                        "nodes": [parts[1], parts[2]],
                        "value": parts[3] if len(parts) > 3 else ""
                    })

            elif designator.startswith("X"):
                subckt = parts[-1]
                components.append({
                    "type": "subcircuit",
                    "designator": designator,
                    "nodes": parts[1:-1],
                    "subcircuit": subckt
                })

            else:
                if len(parts) >= 3:
                    net_name = parts[0]
                    if net_name not in nets:
                        nets[net_name] = []
                    nets[net_name].append({
                        "component": parts[1],
                        "pin": parts[2]
                    })

        return {
            "title": title,
            "components": components,
            "nets": nets,
            "format": "spice"
        }

    def parse_edif(self, netlist: str) -> Dict[str, Any]:
        return {
            "title": "EDIF Netlist",
            "components": [],
            "nets": {},
            "format": "edif",
            "note": "EDIF parsing not implemented in MVP"
        }

    def parse_json(self, netlist: str) -> Dict[str, Any]:
        import json
        try:
            data = json.loads(netlist)
            return data
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")

    def validate_netlist(self, netlist_data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []
        warnings = []

        components = netlist_data.get("components", [])
        nets = netlist_data.get("nets", {})

        if not components:
            errors.append("No components found in netlist")

        all_nodes = set()
        for comp in components:
            nodes = comp.get("nodes", [])
            for node in nodes:
                all_nodes.add(node)

        for net_name, net_nodes in nets.items():
            for node in net_nodes:
                if isinstance(node, dict):
                    node_id = node.get("component")
                    if node_id and node_id not in [c.get("designator") for c in components]:
                        warnings.append(f"Net {net_name} references undefined component {node_id}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "component_count": len(components),
            "net_count": len(nets),
            "node_count": len(all_nodes)
        }
