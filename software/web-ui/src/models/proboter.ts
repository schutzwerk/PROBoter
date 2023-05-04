import type { Vector2D, Vector3D, Matrix3x3, Matrix4x4 } from "./common";

export type ProbeType = "P1" | "P11" | "P2" | "P21";
export type ChannelState = "D" | "A" | "B" | "N";
export type ChannelLevel = "LOW" | "HIGH";
export type PullState = "LOW" | "HIGH";

export interface ReferenceBoard {
  id: number;
  name: string;
  innerBrassPinWidth: number;
  innerBrassPinHeight: number;
  raisedBrassPinWidth: number;
  raisedBrassPinHeight: number;
  thickness: number;
  markerWidth: number;
  markerHeight: number;
  markerGridWidth: number;
  markerGridHeight: number;
  outerWhitePinWidth: number;
  outerWhitePinHeight: number;
  outerBrassPinWidth: number;
  outerBrassPinHeight: number;
}

export interface ProbeCalibrationConfig {
  calibrationFeed: number;
  homeBeforeCalibration: boolean;
  initialProbePositions: Array<Vector3D>;
}

export interface ProboterStatus {
  id: number;
  name: string;
  probes: ProbeType[];
  staticCameras: Array<number>;
  movableCameras: Array<number>;
  hasLightController: boolean;
  hasPicoscope: boolean;
  hasSignalMultiplexer: boolean;
  hasUartAdapter: boolean;
  hasTargetPowerController: boolean;
}

export interface ProbeConfigUpdate {
  name: string;
  tmatToGlob: Matrix4x4;
  posXSafetyPosition: Vector3D;
  negXSafetyPosition: Vector3D;
}

export interface ProbeConfig extends ProbeConfigUpdate {
  probeType: ProbeType;
  orderIndex: number;
}

export interface Probe {
  id: number;
  name: string;
  orderIndex: number;
  probeType: ProbeType;
  connected: boolean;
  moving: boolean;
  currentPositionGlobal: Vector3D;
  currentPositionLocal: Vector3D;
}

export interface ProbeCalibrationResult {
  probe: number;
  tmatLocalToGlobal: Matrix4x4;
  tmatGlobalToLocal: Matrix4x4;
  residualsLocalToGlobal: Array<Vector3D>;
  residualsGlobalToLocal: Array<Vector3D>;
  maxResidualsLocalToGlobal: Vector3D;
  refPinCenters: Array<Vector3D>;
  measuredRefPinCenters: Array<Vector3D>;
}

export interface ProboterConfig {
  id: number;
  name: string;
}

export interface TargetPowerController {
  connected: boolean;
  on: boolean;
}

export interface LightController {
  connected: boolean;
  on: boolean;
}

export interface SignalMultiplexerTestResult {
  channel: number;
  level: ChannelLevel;
}

export interface Camera {
  id: number;
  index: number;
  name: string;
  connected: boolean;
  // Camera resolution as tuple of [width, height] in pixel
  resolution: [number, number];
}

export interface CameraIntrinsicsCalibrationResult {
  cameraMatrix: Matrix3x3;
  distortionCoefficients: [number, number, number, number, number];
}

export interface StaticCameraConfig {
  name: string;
  usbDeviceName: string;
  resolution: [number, number];
  cameraMatrix: Matrix3x3;
  distCoefficients: number[];
  tmatToGlobal: Matrix4x4;
}

export interface StaticCameraCalibrationConfig {
  brightnessThreshold: number;
  imageResolution: Vector2D;
}

export interface StaticCameraCalibrationResult {
  camera: number;
  tmat: Matrix4x4;
  residualsLocalToGlobal: Array<Vector3D>;
  residualsGlobalToLocal: Array<Vector2D>;
  maxResidualsGlobalToLocal: Vector2D;
  maxResidualsImageToGlobal: Vector3D;
}

export interface SignalMultiplexer {
  id: number;
  connectionState: string;
  channelSwitchStates: Array<ChannelState>;
  channelDigitalLevels: Array<ChannelLevel>;
  channelPullStates: Array<PullState>;
}

export interface Picoscope {
  connected: boolean;
}

export interface UartAdapter {
  connected: boolean;
}

export interface PcbScanParameters {
  name: string;
  pcbId: number;
  xRange: [number, number];
  yRange: [number, number];
  zOffset: number;
  imageResolution: [number, number];
}

export interface PcbScanResults {
  scan: number;
}

export type TaskStatus = "SCHEDULED" | "RUNNING" | "CANCELLED" | "ERRORED";

export interface Task {
  id: number;
  name: string;
  progress: number;
  status: TaskStatus;
  error?: string | undefined;
  prameter?: object | undefined;
  result?: object | undefined;
}
