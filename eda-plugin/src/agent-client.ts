import type {
	AgentRequest,
	AgentResponse,
	LayoutResult,
	SimulationResult,
	SimulationConfig,
	AIMessage,
} from './types';

export interface AgentConfig {
	baseUrl: string;
	timeout: number;
	apiKey?: string;
}

export class AgentClient {
	private config: AgentConfig;
	private messageHistory: AIMessage[] = [];
	private wsConnection: WebSocket | null = null;

	constructor(config: AgentConfig) {
		this.config = {
			baseUrl: config.baseUrl || 'http://localhost:8000',
			timeout: config.timeout || 60000,
			apiKey: config.apiKey,
		};
	}

	async sendRequest(request: AgentRequest): Promise<AgentResponse> {
		const url = `${this.config.baseUrl}/api/v1/agent`;

		try {
			const response = await fetch(url, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					...(this.config.apiKey && {
						Authorization: `Bearer ${this.config.apiKey}`,
					}),
				},
				body: JSON.stringify({
					...request,
					history: this.messageHistory.slice(-10),
				}),
				signal: AbortSignal.timeout(this.config.timeout),
			});

			if (!response.ok) {
				throw new Error(`请求失败: ${response.status} ${response.statusText}`);
			}

			const data: AgentResponse = await response.json();

			if (data.success && request.action !== 'chat') {
				this.messageHistory.push({
					role: 'user',
					content: JSON.stringify(request.data),
					timestamp: Date.now(),
				});
				this.messageHistory.push({
					role: 'assistant',
					content: JSON.stringify(data.data),
					timestamp: Date.now(),
					thinking: data.thinking,
				});
			}

			return data;
		} catch (error) {
			console.error('Agent请求失败:', error);
			return {
				success: false,
				message: `请求失败: ${error instanceof Error ? error.message : '未知错误'}`,
			};
		}
	}

	async requestAutoLayout(
		components: unknown[],
		nets: unknown[],
		constraints: unknown[]
	): Promise<LayoutResult | null> {
		const response = await this.sendRequest({
			action: 'layout',
			data: {
				components,
				nets,
				constraints,
			},
		});

		if (response.success && response.data) {
			return response.data as LayoutResult;
		}

		throw new Error(response.message || 'AI布局失败');
	}

	async requestSimulation(
		netlist: string,
		config: SimulationConfig
	): Promise<SimulationResult | null> {
		const response = await this.sendRequest({
			action: 'simulation',
			data: {
				netlist,
				config,
			},
		});

		if (response.success && response.data) {
			return response.data as SimulationResult;
		}

		throw new Error(response.message || '仿真请求失败');
	}

	async analyzeCircuit(components: unknown[], nets: unknown[]): Promise<string | null> {
		const response = await this.sendRequest({
			action: 'analyze',
			data: {
				components,
				nets,
			},
		});

		if (response.success && response.data) {
			return JSON.stringify(response.data);
		}

		throw new Error(response.message || '电路分析失败');
	}

	async chatWithAI(
		message: string,
		context?: { components?: unknown[]; nets?: unknown[] }
	): Promise<{ response: string; thinking?: string }> {
		this.messageHistory.push({
			role: 'user',
			content: message,
			timestamp: Date.now(),
		});

		const response = await this.sendRequest({
			action: 'chat',
			data: {
				message,
				context,
			},
		});

		if (response.success && response.data) {
			const data = response.data as { response: string; thinking?: string };
			this.messageHistory.push({
				role: 'assistant',
				content: data.response,
				timestamp: Date.now(),
				thinking: data.thinking,
			});
			return data;
		}

		throw new Error(response.message || 'AI对话失败');
	}

	async checkConnection(): Promise<boolean> {
		try {
			const response = await fetch(`${this.config.baseUrl}/api/v1/health`, {
				method: 'GET',
				signal: AbortSignal.timeout(5000),
			});
			return response.ok;
		} catch {
			return false;
		}
	}

	async connectWebSocket(onMessage: (data: unknown) => void): Promise<boolean> {
		return new Promise((resolve) => {
			try {
				const wsUrl = this.config.baseUrl.replace('http', 'ws');
				this.wsConnection = new WebSocket(`${wsUrl}/ws/agent`);

				this.wsConnection.onopen = () => {
					console.log('WebSocket连接已建立');
					resolve(true);
				};

				this.wsConnection.onmessage = (event) => {
					try {
						const data = JSON.parse(event.data);
						onMessage(data);
					} catch {
						onMessage(event.data);
					}
				};

				this.wsConnection.onerror = (error) => {
					console.error('WebSocket错误:', error);
					resolve(false);
				};

				this.wsConnection.onclose = () => {
					console.log('WebSocket连接已关闭');
					this.wsConnection = null;
				};
			} catch (error) {
				console.error('WebSocket连接失败:', error);
				resolve(false);
			}
		});
	}

	sendWebSocketMessage(data: unknown): void {
		if (this.wsConnection && this.wsConnection.readyState === WebSocket.OPEN) {
			this.wsConnection.send(JSON.stringify(data));
		}
	}

	disconnectWebSocket(): void {
		if (this.wsConnection) {
			this.wsConnection.close();
			this.wsConnection = null;
		}
	}

	getMessageHistory(): AIMessage[] {
		return [...this.messageHistory];
	}

	clearHistory(): void {
		this.messageHistory = [];
	}

	setApiKey(apiKey: string): void {
		this.config.apiKey = apiKey;
	}

	setBaseUrl(baseUrl: string): void {
		this.config.baseUrl = baseUrl;
	}

	getConfig(): AgentConfig {
		return { ...this.config };
	}
}

export const createAgentClient = (config?: Partial<AgentConfig>): AgentClient => {
	return new AgentClient({
		baseUrl: config?.baseUrl || 'http://localhost:8000',
		timeout: config?.timeout || 60000,
		apiKey: config?.apiKey,
	});
};
