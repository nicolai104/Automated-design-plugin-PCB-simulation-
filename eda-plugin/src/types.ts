export interface ComponentInfo {
	id: string;
	name: string;
	designator: string;
	footprint: string;
	pins: PinInfo[];
	x?: number;
	y?: number;
	rotation?: number;
	priority?: number;
}

export interface PinInfo {
	number: string;
	name: string;
	type: 'input' | 'output' | 'power' | 'signal';
	net?: string;
}

export interface NetInfo {
	name: string;
	nodes: NetNode[];
}

export interface NetNode {
	componentId: string;
	pinNumber: string;
}

export interface LayoutConstraint {
	type: 'forbidden' | 'priority' | 'keepout';
	x: number;
	y: number;
	width: number;
	height: number;
	value?: string;
}

export interface LayoutResult {
	components: ComponentPosition[];
	warnings: string[];
	executionTime: number;
}

export interface ComponentPosition {
	id: string;
	x: number;
	y: number;
	rotation: number;
}

export interface SimulationConfig {
	type: 'DC' | 'AC' | 'Transient';
	parameters: SimulationParams;
}

export interface SimulationParams {
	startFreq?: number;
	endFreq?: number;
	points?: number;
	startTime?: number;
	endTime?: number;
	timeStep?: number;
}

export interface SimulationResult {
	type: string;
	data: number[];
	time?: number[];
	frequency?: number[];
	success: boolean;
	message?: string;
}

export interface AIMessage {
	role: 'user' | 'assistant' | 'system';
	content: string;
	timestamp: number;
	thinking?: string;
}

export interface PanelState {
	isConnected: boolean;
	currentProject?: string;
	components: ComponentInfo[];
	nets: NetInfo[];
	constraints: LayoutConstraint[];
	simulationConfig?: SimulationConfig;
}

export interface AgentRequest {
	action: 'layout' | 'simulation' | 'analyze' | 'chat';
	data: unknown;
	history?: AIMessage[];
}

export interface AgentResponse {
	success: boolean;
	data?: unknown;
	message?: string;
	thinking?: string;
}
