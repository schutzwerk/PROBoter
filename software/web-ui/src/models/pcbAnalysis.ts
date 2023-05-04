import type { Vector2D } from "./common";

export type ComponentPackage =
  | "UNKNOWN"
  | "SON"
  | "SOP"
  | "QFN"
  | "QFP"
  | "BGA"
  | "THT";

export type ComponentType =
  | "UNKNOWN"
  | "IC"
  | "CONN_SMD"
  | "CONN_THT"
  | "IC_UNPOP";

export interface PinDetector {
  id: string;
  name: string;
}

export interface ComponentDetector {
  id: string;
  name: string;
}

export interface PinDetectionResult {
  id: string;
  confidence: number;
  center: [number, number];
}

export interface ComponentDetectionResult {
  id: string;
  package: ComponentPackage;
  confidence: number;
  vendor: string;
  marking: string;
  contour: Vector2D[];
  pins: PinDetectionResult[];
}

export interface PcbVisualAnalysisResult {
  components: ComponentDetectionResult[];
  pads: PinDetectionResult[];
}
