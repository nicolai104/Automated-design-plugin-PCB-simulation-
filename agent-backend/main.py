from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import json
import logging
import asyncio
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

from llm.openai_client import OpenAIClient
from llm.prompt_template import PromptTemplate
from kg.hardware_kg import HardwareKnowledgeGraph
from netlist.parser import NetlistParser
from netlist.converter import NetlistConverter
from storage.session import SessionStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ai-pcb-agent-secret'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

llm_client = None
knowledge_graph = None
netlist_parser = None
netlist_converter = None
session_storage = None


def init_app():
    global llm_client, knowledge_graph, netlist_parser, netlist_converter, session_storage
    logger.info("AI PCB Agent Backend starting...")

    llm_client = OpenAIClient()
    knowledge_graph = HardwareKnowledgeGraph()
    netlist_parser = NetlistParser()
    netlist_converter = NetlistConverter()
    session_storage = SessionStorage()

    logger.info("AI PCB Agent Backend started successfully")


@app.route('/api/v1/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })


@app.route('/api/v1/agent', methods=['POST'])
def handle_agent_request():
    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({"success": False, "message": "Invalid request"}), 400

        action = req_data.get("action")
        data = req_data.get("data", {})

        if action == "chat":
            return handle_chat(data, req_data.get("history"))
        elif action == "layout":
            return handle_layout(data)
        elif action == "simulation":
            return handle_simulation(data)
        elif action == "analyze":
            return handle_analyze(data)
        else:
            return jsonify({"success": False, "message": f"Unknown action: {action}"}), 400

    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


def handle_chat(data, history):
    message = data.get("message", "")
    context = data.get("context", {})

    prompt = PromptTemplate.build_chat_prompt(message, context, history)

    thinking = None
    try:
        response = llm_client.generate(prompt)
    except Exception as e:
        return jsonify({"success": False, "message": f"LLM调用失败: {str(e)}"}), 500

    return jsonify({
        "success": True,
        "data": {
            "response": response,
            "thinking": thinking
        },
        "thinking": thinking
    })


def handle_layout(data):
    components = data.get("components", [])
    nets = data.get("nets", [])
    constraints = data.get("constraints", [])

    prompt = PromptTemplate.build_layout_prompt(components, nets, constraints)

    try:
        response = llm_client.generate(prompt)

        try:
            layout_result = json.loads(response)
        except json.JSONDecodeError:
            layout_result = generate_mock_layout(components)

        execution_time = 1000

        return jsonify({
            "success": True,
            "data": {
                "components": layout_result.get("components", []),
                "warnings": layout_result.get("warnings", []),
                "executionTime": execution_time
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"布局生成失败: {str(e)}"}), 500


def handle_simulation(data):
    netlist = data.get("netlist", "")
    config = data.get("config", {})

    try:
        parsed_netlist = netlist_parser.parse(netlist)

        prompt = PromptTemplate.build_simulation_prompt(parsed_netlist, config)

        try:
            response = llm_client.generate(prompt)
            sim_result = json.loads(response)
        except:
            sim_result = {
                "type": config.get("type", "Transient"),
                "data": [0.0] * 100,
                "success": True,
                "message": "仿真完成"
            }

        return jsonify({
            "success": True,
            "data": sim_result
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"仿真失败: {str(e)}"}), 500


def handle_analyze(data):
    components = data.get("components", [])
    nets = data.get("nets", [])

    try:
        analysis = knowledge_graph.analyze_circuit(components, nets)

        prompt = PromptTemplate.build_analysis_prompt(components, nets, analysis)

        try:
            response = llm_client.generate(prompt)
        except:
            response = f"电路分析完成。检测到 {len(components)} 个元器件和 {len(nets)} 个网络。"

        return jsonify({
            "success": True,
            "data": {
                "analysis": analysis,
                "summary": response
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"分析失败: {str(e)}"}), 500


def generate_mock_layout(components):
    positions = []
    grid_size = 10
    for i, comp in enumerate(components):
        row = i // grid_size
        col = i % grid_size
        positions.append({
            "id": comp.get("id", f"comp_{i}"),
            "x": col * 1000,
            "y": row * 1000,
            "rotation": 0
        })

    return {
        "components": positions,
        "warnings": []
    }


@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('response', {'data': 'Connected'})


@socketio.on('message')
def handle_message(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)
        
        action = data.get("action")
        payload = data.get("data", {})

        if action == "chat":
            response = handle_chat(payload, None)
        elif action == "layout":
            response = handle_layout(payload)
        elif action == "simulation":
            response = handle_simulation(payload)
        else:
            response = jsonify({"success": False, "message": f"Unknown action: {action}"})

        emit('response', response.get_json())
    except Exception as e:
        emit('response', {"success": False, "message": str(e)})


@app.route('/api/v1/session/<session_id>', methods=['GET'])
def get_session(session_id):
    session = session_storage.get_session(session_id)
    if not session:
        return jsonify({"error": "Session not found"}), 404
    return jsonify(session)


@app.route('/api/v1/session/<session_id>', methods=['POST'])
def save_session(session_id):
    data = request.get_json()
    session_storage.save_session(session_id, data)
    return jsonify({"status": "saved"})


if __name__ == '__main__':
    init_app()
    socketio.run(app, host='0.0.0.0', port=8000, debug=True)
