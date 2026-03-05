import type {
	ComponentInfo,
	NetInfo,
	LayoutConstraint,
	ComponentPosition,
	SimulationConfig,
	SimulationResult,
	PanelState,
} from './types';

export class EDAApiClient {
	private panel: unknown = null;
	private currentDocType: 'sch' | 'pcb' | 'none' = 'none';

	constructor() {
		this.detectDocumentType();
	}

	private detectDocumentType(): void {
		try {
			const doc = eda.DMT_EditorControl.getCurrentDocument();
			if (doc) {
				const docType = doc.getType ? doc.getType() : '';
				if (docType === 'SchematicDocument') {
					this.currentDocType = 'sch';
				} else if (docType === 'PCBDocument') {
					this.currentDocType = 'pcb';
				}
			}
		} catch {
			this.currentDocType = 'none';
		}
	}

	async getComponents(): Promise<ComponentInfo[]> {
		this.detectDocumentType();
		if (this.currentDocType === 'none') {
			throw new Error('未检测到打开的文档');
		}

		const components: ComponentInfo[] = [];

		try {
			if (this.currentDocType === 'sch') {
				const schematic = eda.DMT_Schematic.getCurrentSchematic();
				if (schematic) {
					const primitives = schematic.getPrimitives
						? schematic.getPrimitives()
						: [];
					for (const prim of primitives) {
						if (this.isComponent(prim)) {
							components.push(this.extractSchematicComponent(prim));
						}
					}
				}
			} else if (this.currentDocType === 'pcb') {
				const pcb = eda.DMT_Pcb.getCurrentPcb();
				if (pcb) {
					const components_1 = pcb.getComponents
						? pcb.getComponents()
						: [];
					for (const comp of components_1) {
						components.push(this.extractPcbComponent(comp));
					}
				}
			}
		} catch (error) {
			console.error('获取元器件失败:', error);
			throw new Error(`获取元器件失败: ${error}`);
		}

		return components;
	}

	private isComponent(prim: unknown): boolean {
		return (
			prim !== null &&
			typeof prim === 'object' &&
			'getClass' in prim &&
			(prim.getClass?.() === 'Component' ||
				prim.getClass?.() === 'SchematicComponent')
		);
	}

	private extractSchematicComponent(prim: unknown): ComponentInfo {
		const getProp = (prop: string): unknown =>
			prim[prop] ?? prim.getProperty?.(prop);

		return {
			id: String(getProp('uuid') || getProp('id') || ''),
			name: String(getProp('name') || getProp('designator') || ''),
			designator: String(getProp('designator') || ''),
			footprint: String(getProp('footprint') || ''),
			pins: this.extractPins(prim),
			x: Number(getProp('x')) || 0,
			y: Number(getProp('y')) || 0,
			rotation: Number(getProp('rotation')) || 0,
		};
	}

	private extractPcbComponent(comp: unknown): ComponentInfo {
		const getProp = (prop: string): unknown =>
			comp[prop] ?? comp.getProperty?.(prop);

		return {
			id: String(getProp('uuid') || getProp('id') || ''),
			name: String(getProp('name') || getProp('designator') || ''),
			designator: String(getProp('designator') || ''),
			footprint: String(getProp('footprint') || ''),
			pins: [],
			x: Number(getProp('x')) || 0,
			y: Number(getProp('y')) || 0,
			rotation: Number(getProp('rotation')) || 0,
		};
	}

	private extractPins(prim: unknown): { number: string; name: string; type: string }[] {
		const pins: { number: string; name: string; type: string }[] = [];
		try {
			const compPins = prim.getPins ? prim.getPins() : prim.pins;
			if (compPins && Array.isArray(compPins)) {
				for (const pin of compPins) {
					pins.push({
						number: String(pin.number || pin.name || ''),
						name: String(pin.name || ''),
						type: String(pin.type || 'signal'),
					});
				}
			}
		} catch {
			console.warn('提取引脚信息失败');
		}
		return pins;
	}

	async getNets(): Promise<NetInfo[]> {
		this.detectDocumentType();
		const nets: NetInfo[] = [];

		try {
			if (this.currentDocType === 'sch') {
				const schematic = eda.DMT_Schematic.getCurrentSchematic();
				if (schematic) {
					const netlist = schematic.getNetlist
						? schematic.getNetlist()
						: [];
					for (const net of netlist) {
						nets.push({
							name: String(net.name || ''),
							nodes: this.extractNetNodes(net),
						});
					}
				}
			} else if (this.currentDocType === 'pcb') {
				const pcb = eda.DMT_Pcb.getCurrentPcb();
				if (pcb) {
					const nets_1 = pcb.getNets ? pcb.getNets() : [];
					for (const net of nets_1) {
						nets.push({
							name: String(net.name || ''),
							nodes: this.extractNetNodes(net),
						});
					}
				}
			}
		} catch (error) {
			console.error('获取网络失败:', error);
		}

		return nets;
	}

	private extractNetNodes(net: unknown): { componentId: string; pinNumber: string }[] {
		const nodes: { componentId: string; pinNumber: string }[] = [];
		try {
			const netNodes = net.nodes || net.getNodes?.() || [];
			for (const node of netNodes) {
				nodes.push({
					componentId: String(node.componentId || node.component?.id || ''),
					pinNumber: String(node.pinNumber || node.pin || ''),
				});
			}
		} catch {
			console.warn('提取网络节点失败');
		}
		return nodes;
	}

	async generateNetlist(): Promise<string> {
		this.detectDocumentType();

		if (this.currentDocType === 'none') {
			throw new Error('未检测到打开的文档');
		}

		try {
			const schematic = eda.DMT_Schematic.getCurrentSchematic();
			if (schematic) {
				const netlist = schematic.generateNetlist
					? schematic.generateNetlist()
					: await this.buildNetlistFromSchematic();
				return netlist;
			}
		} catch (error) {
			console.error('生成网表失败:', error);
			throw new Error(`生成网表失败: ${error}`);
		}

		throw new Error('无法生成网表');
	}

	private async buildNetlistFromSchematic(): Promise<string> {
		const components = await this.getComponents();
		const nets = await this.getNets();

		let netlist = '* JLCEDA Netlist\n\n';
		netlist += '! Components\n';
		for (const comp of components) {
			netlist += `${comp.designator} ${comp.footprint} ${comp.name}\n`;
		}
		netlist += '\n! Nets\n';
		for (const net of nets) {
			netlist += `${net.name} `;
			for (const node of net.nodes) {
				netlist += `${node.componentId}.${node.pinNumber} `;
			}
			netlist += '\n';
		}

		return netlist;
	}

	async applyLayout(positions: ComponentPosition[]): Promise<boolean> {
		this.detectDocumentType();

		if (this.currentDocType !== 'pcb') {
			throw new Error('需要在PCB文档中执行布局操作');
		}

		try {
			const pcb = eda.DMT_Pcb.getCurrentPcb();
			if (!pcb) {
				throw new Error('无法获取当前PCB文档');
			}

			for (const pos of positions) {
				const component = this.findComponentById(pcb, pos.id);
				if (component) {
					if (component.setPosition) {
						component.setPosition(pos.x, pos.y);
					}
					if (component.setRotation && pos.rotation !== undefined) {
						component.setRotation(pos.rotation);
					}
				}
			}

			pcb.refresh?.();
			return true;
		} catch (error) {
			console.error('应用布局失败:', error);
			throw new Error(`应用布局失败: ${error}`);
		}
	}

	private findComponentById(pcb: unknown, id: string): unknown {
		const components = pcb.getComponents ? pcb.getComponents() : [];
		for (const comp of components) {
			if (comp.id === id || comp.uuid === id) {
				return comp;
			}
		}
		return null;
	}

	async setForbiddenZone(constraint: LayoutConstraint): Promise<boolean> {
		this.detectDocumentType();

		if (this.currentDocType !== 'pcb') {
			throw new Error('需要在PCB文档中设置禁止区域');
		}

		try {
			const pcb = eda.DMT_Pcb.getCurrentPcb();
			if (!pcb) {
				throw new Error('无法获取当前PCB文档');
			}

			const region = eda.PCB_PrimitiveRegion.create
				? eda.PCB_PrimitiveRegion.create()
				: {};

			if (region.setRegionType) {
				region.setRegionType('Forbidden');
			}
			if (region.setPoints) {
				const points = [
					{ x: constraint.x, y: constraint.y },
					{ x: constraint.x + constraint.width, y: constraint.y },
					{ x: constraint.x + constraint.width, y: constraint.y + constraint.height },
					{ x: constraint.x, y: constraint.y + constraint.height },
				];
				region.setPoints(points);
			}

			pcb.addPrimitive?.(region);
			pcb.refresh?.();
			return true;
		} catch (error) {
			console.error('设置禁止区域失败:', error);
			throw new Error(`设置禁止区域失败: ${error}`);
		}
	}

	async exportPCB(): Promise<string> {
		try {
			const pcb = eda.DMT_Pcb.getCurrentPcb();
			if (pcb && pcb.export) {
				const exportPath = await pcb.export('Gerber');
				return exportPath;
			}
		} catch (error) {
			console.error('导出PCB失败:', error);
			throw new Error(`导出PCB失败: ${error}`);
		}
		throw new Error('无法导出PCB');
	}

	getCurrentDocumentType(): 'sch' | 'pcb' | 'none' {
		this.detectDocumentType();
		return this.currentDocType;
	}

	async getPanelState(): Promise<PanelState> {
		const components = await this.getComponents();
		const nets = await this.getNets();

		return {
			isConnected: true,
			currentProject: this.getCurrentProjectName(),
			components,
			nets,
			constraints: [],
		};
	}

	private getCurrentProjectName(): string {
		try {
			const project = eda.DMT_Project.getCurrentProject();
			return project?.name || '未命名项目';
		} catch {
			return '未命名项目';
		}
	}

	showMessage(message: string, type: 'info' | 'warning' | 'error' = 'info'): void {
		if (type === 'error') {
			eda.sys_Dialog.showErrorMessage(message, 'AI PCB助手');
		} else if (type === 'warning') {
			eda.sys_Dialog.showWarningMessage(message, 'AI PCB助手');
		} else {
			eda.sys_Dialog.showInformationMessage(message, 'AI PCB助手');
		}
	}

	log(message: string): void {
		console.log(`[AI PCB Agent] ${message}`);
		if (eda.SYS_Log) {
			eda.SYS_Log.info?.(`[AI PCB Agent] ${message}`);
		}
	}
}

export const edaApi = new EDAApiClient();
