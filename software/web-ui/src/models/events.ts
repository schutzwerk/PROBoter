import type { Vector3D } from "./common";
import type {
  LightController,
  Probe,
  ProbeType,
  TargetPowerController,
} from "./proboter";

export interface TaskScheduledEvent {
  id: number;
  name: string;
}

export interface TaskStartedEvent {
  id: number;
  name: string;
}

export interface TaskFinishedEvent {
  id: number;
  name: string;
  cancelled: boolean;
  hadError: boolean;
}

export interface ProbeStatusChangedEvent {
  id: number;
  status: Probe;
}
export interface ProbeMoveStartEvent {
  probeType: ProbeType;
  startLocal: Vector3D;
  startGlobal: Vector3D;
  destinationLocal: Vector3D;
  destinationGlobal: Vector3D;
  feed: number;
}

export interface ProbeMoveFinishedEvent {
  probeType: ProbeType;
}

export interface TargetPowerControllerChangedEvent {
  status: TargetPowerController;
}

export interface LightControllerChangedEvent {
  status: LightController;
}

export type Event = {
  TaskStartedEvent: TaskStartedEvent;
  TaskFinishedEvent: TaskFinishedEvent;
  ProbeStatusChangedEvent: ProbeStatusChangedEvent;
  ProbeMoveStartEvent: ProbeMoveStartEvent;
  ProbeMoveFinishedEvent: ProbeMoveFinishedEvent;
  TargetPowerControllerChangedEvent: TargetPowerControllerChangedEvent;
  LightControllerChangedEvent: LightControllerChangedEvent;
};
type ValueOf<T> = T[keyof T];
export type EventData = ValueOf<Event>;

export enum Events {
  TaskStartedEvent = "TaskStartedEvent",
  TaskFinishedEvent = "TaskFinishedEvent",
  ProbeStatusChangedEvent = "ProbeStatusChangedEvent",
  ProbeMoveStartEvent = "ProbeMoveStartEvent",
  ProbeMoveFinishedEvent = "ProbeMoveFinishedEvent",
  TargetPowerControllerChangedEvent = "TargetPowerControllerChangedEvent",
  LightControllerChangedEvent = "LightControllerChangedEvent",
}
