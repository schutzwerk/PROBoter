import mitt from "mitt";
import type { Event } from "./models";

const emitter = mitt<Event>();

const FAKE_IT_TILL_PROBOTER_MAKES_IT = true;

const backendConfig = {
  pcbApi: "",
  proboterApi: "",
  proboterEventApi: "",
  pcbAnalysisApi: "",
  signalAnalysisApi: "",
};

const devBackendConfig = {
  pcbApi: "http://" + location.hostname + ":5000/api/v1",
  proboterApi: "http://" + location.hostname + ":5003/api/v1",
  proboterEventApi: "ws://" + location.hostname + ":5003/api/v1",
  pcbAnalysisApi: "http://" + location.hostname + ":5001/api/v1",
  signalAnalysisApi: "http://" + location.hostname + ":5002/api/v1",
};

const prodBackendConfig = {
  pcbApi: "/api/storage",
  proboterApi: "/api/hardware",
  proboterEventApi: "wss://" + location.host + "/api/hardware",
  pcbAnalysisApi: "/api/pcb-analysis",
  signalAnalysisApi: "/api/signal-analysis",
};

const loggerConfig = {
  isEnabled: true,
  logLevel: "debug",
  stringifyArguments: false,
  showLogLevel: true,
  showMethodName: true,
  separator: "|",
  showConsoleColors: true,
};

export {
  backendConfig,
  devBackendConfig,
  prodBackendConfig,
  loggerConfig,
  emitter,
  FAKE_IT_TILL_PROBOTER_MAKES_IT,
};
