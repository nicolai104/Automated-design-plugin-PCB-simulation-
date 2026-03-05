import { edaApi } from './eda-api';
import { createAgentClient, type AgentClient } from './agent-client';
import type { LayoutResult, SimulationConfig, SimulationResult } from './types';

let agentClient: AgentClient | null = null;
let currentPanel: unknown = null;

function getAgentClient(): AgentClient {
	if (!agentClient) {
		agentClient = createAgentClient({
			baseUrl: 'http://localhost:8000',
			timeout: 60000,
		});
	}
	return agentClient;
}

export function activate(status?: 'onStartupFinished', _arg?: string): void {
	edaApi.log('AI PCB Agent 插件已激活');

	initializeAgent();
}

async function initializeAgent(): Promise<void> {
	try {
		const client = getAgentClient();
		const isConnected = await client.checkConnection();

		if (isConnected) {
			edaApi.log('AI Agent服务已连接');
		} else {
			edaApi.log('AI Agent服务未连接，请确保后端服务已启动');
		}
	} catch (error) {
		edaApi.log(`初始化AI Agent失败: ${error}`);
	}
}

export function openPanel(): void {
	try {
		const panelId = 'ai-pcb-panel';

		if (eda.SYS_PanelControl && eda.SYS_PanelControl.showPanel) {
			eda.SYS_PanelControl.showPanel(panelId);
			currentPanel = panelId;
			edaApi.log('AI助手面板已打开');
		} else if (eda.SYS_IFrame && eda.SYS_IFrame.create) {
			eda.SYS_IFrame.create({
				id: panelId,
				title: 'AI PCB设计助手',
				url: './iframe/index.html',
				width: 380,
				height: 600,
			});
			currentPanel = panelId;
			edaApi.log('AI助手面板已打开');
		} else {
			eda.sys_Dialog.showInformationMessage(
				'AI PCB设计助手面板将在右侧边栏显示',
				'AI PCB助手'
			);
		}
	} catch (error) {
		console.error('打开面板失败:', error);
		edaApi.showMessage(`打开面板失败: ${error}`, 'error');
	}
}

export async function autoLayout(): Promise<void> {
	try {
		edaApi.log('开始AI自动布局...');

		const docType = edaApi.getCurrentDocumentType();
		if (docType !== 'pcb') {
			throw new Error('请在PCB文档中执行自动布局');
		}

		edaApi.showMessage('正在获取元器件信息...', 'info');

		const components = await edaApi.getComponents();
		const nets = await edaApi.getNets();

		if (components.length === 0) {
			throw new Error('未找到元器件，请先添加元器件');
		}

		edaApi.log(`获取到 ${components.length} 个元器件, ${nets.length} 个网络`);

		const client = getAgentClient();
		edaApi.showMessage('AI正在生成布局方案...', 'info');

		const layoutResult = await client.requestAutoLayout(components, nets, []);

		if (layoutResult) {
			await edaApi.applyLayout(layoutResult.components);

			edaApi.log(`布局完成，耗时 ${layoutResult.executionTime}ms`);
			edaApi.showMessage(
				`AI布局完成！\n元器件数量: ${components.length}\n耗时: ${layoutResult.executionTime}ms\n警告: ${layoutResult.warnings.length}个`,
				'info'
			);
		}
	} catch (error) {
		const errorMessage = error instanceof Error ? error.message : String(error);
		edaApi.log(`AI布局失败: ${errorMessage}`);
		edaApi.showMessage(`AI布局失败: ${errorMessage}`, 'error');
	}
}

export async function runSimulation(config?: SimulationConfig): Promise<void> {
	try {
		edaApi.log('开始电路仿真...');

		const docType = edaApi.getCurrentDocumentType();
		if (docType !== 'sch') {
			throw new Error('请在原理图文档中执行仿真');
		}

		edaApi.showMessage('正在生成网表...', 'info');

		const netlist = await edaApi.generateNetlist();
		edaApi.log(`网表已生成，长度: ${netlist.length} 字符`);

		const simulationConfig: SimulationConfig = config || {
			type: 'Transient',
			parameters: {
				startTime: 0,
				endTime: 0.001,
				timeStep: 0.000001,
			},
		};

		const client = getAgentClient();
		edaApi.showMessage('正在运行仿真...', 'info');

		const result = await client.requestSimulation(netlist, simulationConfig);

		if (result) {
			edaApi.log(`仿真完成: ${result.message || '成功'}`);
			edaApi.showMessage(
				`仿真完成!\n类型: ${result.type}\n结果: ${result.message || '成功'}`,
				'info'
			);
		}
	} catch (error) {
		const errorMessage = error instanceof Error ? error.message : String(error);
		edaApi.log(`仿真失败: ${errorMessage}`);
		edaApi.showMessage(`仿真失败: ${errorMessage}`, 'error');
	}
}

export async function analyzeCircuit(): Promise<void> {
	try {
		edaApi.log('开始电路分析...');

		const components = await edaApi.getComponents();
		const nets = await edaApi.getNets();

		const client = getAgentClient();
		edaApi.showMessage('AI正在分析电路...', 'info');

		const analysis = await client.analyzeCircuit(components, nets);

		if (analysis) {
			edaApi.log('电路分析完成');
			edaApi.showMessage(`电路分析完成:\n${analysis}`, 'info');
		}
	} catch (error) {
		const errorMessage = error instanceof Error ? error.message : String(error);
		edaApi.log(`电路分析失败: ${errorMessage}`);
		edaApi.showMessage(`电路分析失败: ${errorMessage}`, 'error');
	}
}

export async function chatWithAI(message: string): Promise<string> {
	try {
		const client = getAgentClient();
		const components = await edaApi.getComponents();
		const nets = await edaApi.getNets();

		const result = await client.chatWithAI(message, { components, nets });
		return result.response;
	} catch (error) {
		const errorMessage = error instanceof Error ? error.message : String(error);
		return `抱歉，处理您的请求时发生错误: ${errorMessage}`;
	}
}

export function showAbout(): void {
	const version = '1.0.0';
	const description = `AI PCB设计助手 v${version}

基于大模型与知识图谱驱动的PCB设计+仿真一体化自动化插件

核心功能:
• AI自动布局
• 电路仿真
• 电路分析
• 智能对话

© 2024 AI PCB Team`;

	eda.sys_Dialog.showInformationMessage(description, '关于 AI PCB设计助手');
}

export function getAgentStatus(): { connected: boolean; version: string } {
	const client = getAgentClient();
	return {
		connected: false,
		version: '1.0.0',
	};
}
