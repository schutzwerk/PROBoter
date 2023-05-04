import axios from "axios";
import { backendConfig } from "@/globals";
import { Buffer } from "buffer";
import log from "js-vue-logger";

import type {
  ProboterStatus,
  Probe,
  ProbeType,
  ProbeConfig,
  Camera,
  StaticCameraConfig,
  ReferenceBoard,
  ProbeCalibrationConfig,
  Vector3D,
  ProbeCalibrationResult,
  ProbeConfigUpdate,
  StaticCameraCalibrationConfig,
  StaticCameraCalibrationResult,
  CameraIntrinsicsCalibrationResult,
  SignalMultiplexer,
  SignalMultiplexerTestResult,
  PcbScanParameters,
  PcbScanResults,
  Pad,
  Task,
} from "@/models";

export interface ProboterErrorResponse {
  reason: string;
  description: string;
}

export class ProboterError extends Error {
  reason: string;
  description: string;
  constructor(response: ProboterErrorResponse) {
    super(response.reason);
    this.name = "ProboterError";
    this.reason = response.reason;
    this.description = response.description;
  }
}

export default {
  /********************************
   *
   * Global PROBoter operations
   *
   ********************************/
  async getProboterStatus(): Promise<ProboterStatus> {
    return axios
      .get(backendConfig.proboterApi + "/proboter")
      .then((response) => response.data);
  },

  async homeProboter(): Promise<ProboterStatus> {
    return axios
      .post(backendConfig.proboterApi + "/proboter/home")
      .then((response) => response.data);
  },

  async clearProbingArea(): Promise<ProboterStatus> {
    return axios
      .post(backendConfig.proboterApi + "/proboter/clear-probing-area")
      .then((response) => response.data);
  },

  async reconnectProboter(): Promise<ProboterStatus> {
    return axios
      .post(backendConfig.proboterApi + "/proboter/reconnect")
      .then((response) => response.data);
  },

  /********************************
   *
   * Probe Configuration
   *
   ********************************/
  async getProbeConfig(probe: Probe): Promise<ProbeConfig> {
    return axios
      .get(backendConfig.proboterApi + "/probe/" + probe.probeType + "/config")
      .then((response) => response.data);
  },

  async updateProbeConfig(
    probe: Probe,
    probeConfig: ProbeConfigUpdate
  ): Promise<ProbeConfig> {
    return axios
      .put(
        backendConfig.proboterApi + "/probe/" + probe.probeType + "/config",
        probeConfig
      )
      .then((response) => response.data)
      .catch((error) => {
        throw new Error(error.response.data);
      });
  },

  async getProbeCalibrationConfig(
    probe: Probe
  ): Promise<ProbeCalibrationConfig> {
    return axios
      .get(
        backendConfig.proboterApi +
          "/probe/" +
          probe.probeType +
          "/calibration-config"
      )
      .then((response) => response.data);
  },

  async updateProbeCalibrationConfig(
    probe: Probe,
    calibrationConfig: ProbeCalibrationConfig
  ): Promise<ProbeCalibrationConfig> {
    return axios
      .put(
        backendConfig.proboterApi +
          "/probe/" +
          probe.probeType +
          "/calibration-config",
        calibrationConfig
      )
      .then((response) => response.data)
      .catch((error) => {
        throw new ProboterError(error.response.data);
      });
  },

  /********************************
   *
   * Reference / calibration board
   * operations
   *
   ********************************/
  async getReferenceBoards(): Promise<Array<ReferenceBoard>> {
    return axios
      .get(backendConfig.proboterApi + "/reference-board")
      .then((response) => response.data.referenceBoards);
  },

  /********************************
   *
   * Probe operations
   *
   ********************************/
  async getProbeStatus(probeType: ProbeType) {
    return axios
      .get(backendConfig.proboterApi + "/probe/" + probeType)
      .then((response) => response.data);
  },

  async homeProbe(probe: Probe): Promise<Probe> {
    return axios
      .post(backendConfig.proboterApi + "/probe/" + probe.probeType + "/home")
      .then((response) => {
        return response.data;
      })
      .catch((error) => error.response.data);
  },

  async moveProbe(
    probe: Probe,
    position: number[],
    feed = 1000,
    isGlobal = false
  ): Promise<Probe> {
    const parameters = {
      position: position,
      feed: feed,
      isGlobal: isGlobal,
    };
    return axios
      .post(
        backendConfig.proboterApi + "/probe/" + probe.probeType + "/move",
        parameters
      )
      .then((response) => {
        return response.data;
      })
      .catch((error) => {
        throw new Error(error.response.data);
      });
  },

  async calibrateProbe(
    probe: Probe,
    referenceBoard: ReferenceBoard,
    initialProbePositions: Array<Vector3D>,
    feed = 1000,
    homeBeforeCalibration = true,
    numCalibrationRuns = 1
  ): Promise<Array<ProbeCalibrationResult>> {
    const calibrationParameters = {
      referenceBoard: referenceBoard.id,
      initialProbePositions: initialProbePositions,
      calibrationFeed: feed,
      homeBeforeCalibration: homeBeforeCalibration,
      numCalibrationRuns: numCalibrationRuns,
    };
    return axios
      .post(
        backendConfig.proboterApi + "/probe/" + probe.probeType + "/calibrate",
        calibrationParameters
      )
      .then((response) => response.data.results)
      .catch((error) => {
        throw new ProboterError(error.response.data);
      });
  },

  /********************************
   *
   * Light controller operations
   *
   ********************************/
  async getLightStatus() {
    return axios
      .get(backendConfig.proboterApi + "/light")
      .then((response) => response.data);
  },

  async switchLight(on = true) {
    let cmdUrl = backendConfig.proboterApi + "/light/";
    cmdUrl += on ? "on" : "off";
    return axios.post(cmdUrl).then((response) => response.data);
  },

  /********************************
   *
   * Target power switch operations
   *
   ********************************/
  async getPowerState() {
    return axios
      .get(backendConfig.proboterApi + "/power-controller")
      .then((response) => response.data);
  },

  async switchPower(on = true) {
    let cmdUrl = backendConfig.proboterApi + "/power-controller/";
    cmdUrl += on ? "on" : "off";
    return axios.post(cmdUrl).then((response) => response.data);
  },

  async resetTarget() {
    const cmdUrl = backendConfig.proboterApi + "/power-controller/reset";
    return axios.post(cmdUrl).then((response) => response.data);
  },

  /********************************
   *
   * Generic camera operations
   *
   ********************************/
  async getCameraStatus(
    camera_idx: number,
    is_movable = false
  ): Promise<Camera> {
    let configUrl = backendConfig.proboterApi + "/camera";
    if (is_movable) {
      configUrl += "/movable/" + camera_idx;
    } else {
      configUrl += "/static/" + camera_idx;
    }
    return axios.get(configUrl).then((response) => {
      const cameraStatus = response.data;
      return cameraStatus;
    });
  },

  getStaticCameraFeedUrl: function (cameraIndex: number): string {
    let endpointUrl = backendConfig.proboterApi + "/camera/static";
    endpointUrl += "/" + cameraIndex + "/feed";
    return endpointUrl;
  },

  getMovableCameraFeedUrl: function (camera: Camera): URL {
    let endpointUrl = backendConfig.proboterEventApi + "/camera/movable";
    endpointUrl += "/" + camera.index + "/feed";
    return new URL(endpointUrl);
  },

  async takeStaticCameraSnapshot(
    camera: Camera,
    width = 1920,
    height = 1080,
    undistort = false
  ): Promise<string> {
    // Take a camera snapshot
    const queryParameter = {
      width: width,
      height: height,
      undistort: undistort,
    };
    return axios
      .get(
        backendConfig.proboterApi +
          "/camera/static/" +
          camera.index +
          "/snapshot",
        { params: queryParameter, responseType: "arraybuffer" }
      )
      .then((response) => {
        const base64 = Buffer.from(response.data, "binary").toString("base64");
        return `data:${response.headers[
          "content-type"
        ].toLowerCase()};base64,${base64}`;
      });
  },

  async calibrateStaticCameraIntrinsicParameters(
    camera: Camera,
    is_movable: boolean,
    snapshots: Array<File>,
    gridSize: [number, number] = [10, 6],
    fieldSize: [number, number] = [10, 10]
  ): Promise<CameraIntrinsicsCalibrationResult> {
    // Build the form data
    const formData = new FormData();
    formData.append("gridSizeX", gridSize[0].toString());
    formData.append("gridSizeY", gridSize[1].toString());
    formData.append("fieldSizeX", fieldSize[0].toString());
    formData.append("fieldSizeY", fieldSize[1].toString());
    // Trigger the calibration in the backend
    snapshots.forEach((snapshot) => formData.append("snapshots", snapshot));
    return axios
      .post(
        backendConfig.proboterApi +
          "/camera/" +
          (is_movable ? "movable" : "static") +
          "/" +
          camera.index +
          "/calibrate-intrinsics",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      )
      .then((response) => response.data)
      .catch((error) => {
        throw new ProboterError(error.response.data);
      });
  },

  /********************************
   *
   * Static camera operations
   *
   ********************************/
  async getStaticCameraConfig(camera: Camera): Promise<StaticCameraConfig> {
    let configUrl = backendConfig.proboterApi + "/camera/static/";
    configUrl += camera.index;
    configUrl += "/config";
    return axios.get(configUrl).then((response) => response.data);
  },

  async updateStaticCameraConfig(
    camera: Camera,
    cameraConfig: StaticCameraConfig
  ): Promise<StaticCameraConfig> {
    let configUrl = backendConfig.proboterApi + "/camera/static/";
    configUrl += camera.index;
    configUrl += "/config";
    return axios
      .put(configUrl, cameraConfig)
      .then((response) => response.data)
      .catch((error) => {
        throw new Error(error.response.data);
      });
  },

  async getStaticCameraCalibrationConfig(
    camera: Camera
  ): Promise<StaticCameraCalibrationConfig> {
    let configUrl = backendConfig.proboterApi + "/camera/static/";
    configUrl += camera.index;
    configUrl += "/calibration-config";
    return axios.get(configUrl).then((response) => response.data);
  },

  async updateStaticCameraCalibrationConfig(
    camera: Camera,
    calibrationConfig: StaticCameraCalibrationConfig
  ): Promise<StaticCameraCalibrationConfig> {
    let configUrl = backendConfig.proboterApi + "/camera/static/";
    configUrl += camera.index;
    configUrl += "/calibration-config";
    return axios
      .put(configUrl, calibrationConfig)
      .then((response) => response.data)
      .catch((error) => {
        throw new ProboterError(error.response.data);
      });
  },

  async calibrateStaticCamera(
    camera: Camera,
    referenceBoardId: number,
    brightnessThreshold: number,
    imageResolution: [number, number],
    numCalibrationRuns = 1
  ): Promise<Array<StaticCameraCalibrationResult>> {
    const url =
      backendConfig.proboterApi +
      "/camera/static/" +
      camera.index +
      "/calibrate";
    return axios
      .post(url, {
        referenceBoard: referenceBoardId,
        brightnessThreshold: brightnessThreshold,
        imageResolution: imageResolution,
        numCalibrationRuns: numCalibrationRuns,
      })
      .then((response) => response.data.results)
      .catch((error) => {
        throw new ProboterError(error.response.data);
      });
  },

  /********************************
   *
   * Signal multiplexer operations
   *
   ********************************/
  async getMultiplexerStatus(): Promise<SignalMultiplexer> {
    return axios
      .get(backendConfig.proboterApi + "/signal-multiplexer")
      .then((response) => response.data);
  },

  async connectChannelToAnalog(channel: number): Promise<SignalMultiplexer> {
    return axios
      .post(
        backendConfig.proboterApi +
          "/signal-multiplexer/route-to-analog/" +
          channel
      )
      .then((response) => response.data);
  },

  async pullChannel(channel: number): Promise<SignalMultiplexer> {
    return axios
      .post(backendConfig.proboterApi + "/signal-multiplexer/pull/" + channel)
      .then((response) => response.data);
  },

  async releaseChannel(channel: number): Promise<SignalMultiplexer> {
    return axios
      .post(
        backendConfig.proboterApi + "/signal-multiplexer/release/" + channel
      )
      .then((response) => response.data);
  },

  async releaseAll(): Promise<SignalMultiplexer> {
    return axios
      .post(backendConfig.proboterApi + "/signal-multiplexer/release-all")
      .then((response) => response.data);
  },

  async switchDigital(channel: number): Promise<SignalMultiplexer> {
    return axios
      .post(
        backendConfig.proboterApi +
          "/signal-multiplexer/route-to-digital/" +
          channel
      )
      .then((response) => response.data);
  },

  async testChannel(channel: number): Promise<SignalMultiplexerTestResult> {
    return axios
      .post(
        backendConfig.proboterApi + "/signal-multiplexer/test-level/" + channel
      )
      .then((response) => response.data);
  },
  /********************************
   *
   * UART / serial USB adapter operations
   *
   ********************************/
  async activateUartAdapterAsyncListening() {
    return axios.post(backendConfig.proboterApi + "/uart-interface/activate");
  },

  async deactivateUartAdapterAsyncListening() {
    return axios.post(backendConfig.proboterApi + "/uart-interface/deactivate");
  },

  createUartShellSocket: function () {
    return new WebSocket(
      backendConfig.proboterEventApi + "/uart-interface/shell"
    );
  },

  /********************************
   *
   * UART / probing operations
   *
   ********************************/
  async probeUartInterface(rxPin: Pad, txPin: Pad, baudrate: number) {
    return axios
      .post(backendConfig.proboterApi + "/probing/uart", {
        pcb: rxPin.pcbId,
        rxPin: rxPin.id,
        txPin: txPin.id,
        baudrate: baudrate,
      })
      .then((response) => response.data)
      .catch((error) => {
        throw new Error(error.response.data);
      });
  },

  /********************************
   *
   * High-level scan operations
   *
   ********************************/
  async createPcbScanWithStaticCamera(
    camera: Camera,
    parameters: PcbScanParameters
  ): Promise<PcbScanResults> {
    return axios
      .post(
        backendConfig.proboterApi + "/camera/static/" + camera.index + "/scan",
        parameters
      )
      .then((response) => response.data);
  },

  /********************************
   *
   * High-level probing operations
   *
   ********************************/
  async probePinConnectivity(
    pcbId: number,
    pins: Pad[],
    probes: ProbeType[],
    feed = 1000,
    zOffset = 0.0
  ): Promise<void> {
    return axios
      .post(backendConfig.proboterApi + "/probing/electrical-connectivity", {
        pcb: pcbId,
        pins: pins.map((pin) => pin.id),
        probes: probes,
        feed: feed,
        zOffset: zOffset,
      })
      .then((response) => response.data)
      .catch((error) => {
        throw new Error(error.response.data);
      });
  },

  async measureVoltageSignals(
    pcbId: number,
    pinIds: Array<number>,
    triggerSource: string,
    triggerLevel: number,
    timeResolution: number,
    duration: number,
    zOffset: number
  ) {
    log.info("Start voltage signal measurement");

    return axios
      .post(backendConfig.proboterApi + "/probing/measure-voltage-signals", {
        pcb: pcbId,
        pins: pinIds,
        triggerSource: triggerSource,
        triggerLevel: triggerLevel,
        timeResolution: timeResolution,
        duration: duration,
        zOffset: zOffset,
      })
      .then((response) => response.data);
  },

  /********************************
   *
   * Demo mode
   *
   ********************************/
  async demoProbeParty(feed: number, z_offset: number): Promise<number> {
    log.info("Start demo mode");
    return axios
      .post(backendConfig.proboterApi + "/demo-mode/probe-party", {
        feed: feed,
        z_offset: z_offset,
      })
      .then((response) => response.data.id);
  },

  /********************************
   *
   * Task
   *
   ********************************/
  async taskGetCurrent(): Promise<Task | undefined> {
    return axios
      .get(backendConfig.proboterApi + "/tasks/current")
      .then((response) => {
        if (response.status == 204) {
          return undefined;
        }

        return response.data;
      });
  },

  async taskCancelCurrent(): Promise<void> {
    return axios.post(backendConfig.proboterApi + "/tasks/cancel");
  },
};
