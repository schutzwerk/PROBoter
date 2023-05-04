export interface Entity {
  id: number;
  name: string;
}

export interface VisualEntity extends Entity {
  isVisible: boolean;
  isTemporary: boolean;
}

export interface Pad extends VisualEntity {
  center: Array<number>;
  pcbId: number;
  componentId: number | undefined;
  networkId: number | undefined;
}

export interface Component extends VisualEntity {
  vendor: string;
  marking: string;
  package: string;
  contour: Array<Array<number>>;
  pcbId: number;
}

export interface Network extends VisualEntity {
  pinIds: Array<number>;
  pcbId: number;
}

export interface Scan extends VisualEntity {
  numImages: number;
  scanImages: Array<number>;
  xMin: number;
  xMax: number;
  yMin: number;
  yMax: number;
  zOffset: number;
  pcbId: number;
}

export interface Pcb extends Entity {
  name: string;
  description: string;
  thickness: number;
  numScans: number;
  numComponents: number;
  numNetworks: number;
  networks: Array<Network>;
  components: Array<Component>;
  pads: Array<Pad>;
  scans: Array<Scan>;
}
