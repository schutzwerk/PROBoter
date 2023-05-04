import { proboter } from "@/api";
import { defineStore } from "pinia";
import log from "js-vue-logger";

import type {
  Probe,
  ProbeConfig,
  ProbeType,
  ProboterConfig,
  TargetPowerController,
  LightController,
  SignalMultiplexer,
  Camera,
  Picoscope,
  UartAdapter,
  StaticCameraConfig,
  Task,
} from "@/models";

export const useProboterStore = defineStore("proboter", {
  state: () => ({
    proboterConfig: undefined as ProboterConfig | undefined,
    probes: [] as Probe[],
    staticCameras: [] as Camera[],
    movableCameras: [] as Camera[],
    light: undefined as LightController | undefined,
    power: undefined as TargetPowerController | undefined,
    signalMultiplexer: undefined as SignalMultiplexer | undefined,
    picoscope: undefined as Picoscope | undefined,
    uart_adapter: undefined as UartAdapter | undefined,
    currentTask: undefined as Task | undefined,
  }),

  getters: {
    getProbeByType: (state) => {
      return (probeType: ProbeType): Probe | undefined =>
        state.probes.find((probe) => probe.probeType === probeType);
    },
    getStaticCameraByIndex: (state) => {
      return (cameraIndex: number): Camera | undefined =>
        state.staticCameras.find((camera) => camera.index === cameraIndex);
    },
  },

  actions: {
    /***************************************
     *
     * PROBoter actions
     *
     ***************************************/
    async syncProboterState() {
      proboter.getProboterStatus().then(async (proboter) => {
        // Cache the current config
        this.proboterConfig = {
          id: proboter.id,
          name: proboter.name,
        };
        // Sync with the PROBoter hardware
        const promises = [];
        promises.push(this.syncProbes(proboter.probes));
        promises.push(this.syncStaticCameras(proboter.staticCameras));
        promises.push(this.syncMovableCameras(proboter.movableCameras));
        if (proboter.hasLightController) {
          promises.push(this.syncLightControllerStatus());
        }
        if (proboter.hasTargetPowerController) {
          promises.push(this.syncTargetPowerControllerStatus());
        }
        if (proboter.hasSignalMultiplexer) {
          promises.push(this.syncSignalMultiplexer());
        }
        if (proboter.hasUartAdapter) {
          this.uart_adapter = { connected: true };
        }
        if (proboter.hasPicoscope) {
          this.picoscope = { connected: true };
        }
        promises.push(this.syncProboterCurrentTask());
        return Promise.all(promises).then(() => {
          return proboter;
        });
      });
    },

    async reconnectProboter() {
      return proboter.reconnectProboter().then(() => {
        return this.syncProboterState();
      });
    },

    async homeProboter() {
      return proboter.homeProboter();
    },

    /***************************************
     *
     * Probe actions
     *
     ***************************************/
    async syncProbes(probeTypes: ProbeType[]) {
      const probeStatusRequests = probeTypes.map(async (probeType) => {
        return proboter.getProbeStatus(probeType).then((probe) => {
          return probe;
        });
      });

      return Promise.all(probeStatusRequests).then((probes) => {
        probes.forEach((p) => {
          const probeIdx = this.probes.findIndex((pp) => pp.id == p.id);
          if (probeIdx >= 0) {
            this.probes[probeIdx] = p;
          } else {
            this.probes.push(p);
          }
        });
      });
    },

    async fetchProbeByType(probeType: ProbeType) {
      return this.syncProbes([probeType]).then(() => {
        return this.probes.find((probe) => probe.probeType === probeType);
      });
    },

    async homeProbe(probe: Probe): Promise<void> {
      return proboter.homeProbe(probe).then((newProbe) => {
        this.probes.map((p) => (p.id == newProbe.id ? newProbe : p));
      });
    },

    async moveProbe(
      probe: Probe,
      position: number[],
      feed = 1000,
      isGlobal = false
    ) {
      return proboter
        .moveProbe(probe, position, feed, isGlobal)
        .then((newProbe) => {
          this.probes = this.probes.map((p) =>
            p.id == newProbe.id ? newProbe : p
          );
        });
    },

    /***************************************
     *
     * Camera actions
     *
     ***************************************/
    async syncStaticCameras(cameraIdxs: number[]) {
      // Sync the camera configs
      const cameraStatusRequests = cameraIdxs.map(async (idx) => {
        return proboter.getCameraStatus(idx, false).then((camera) => {
          return camera;
        });
      });

      return Promise.all(cameraStatusRequests).then((cameras) => {
        cameras.forEach((c) => {
          const cameraIdx = this.staticCameras.findIndex(
            (cc) => cc.index == c.index
          );
          if (cameraIdx >= 0) {
            this.staticCameras[cameraIdx] = c;
          } else {
            this.staticCameras.push(c);
          }
        });
      });
    },

    async fetchStaticCameraByIndex(cameraIndex: number) {
      return this.syncStaticCameras([cameraIndex]).then(() => {
        return this.staticCameras.find(
          (camera) => camera.index === cameraIndex
        );
      });
    },

    async syncMovableCameras(cameraIdxs: number[]) {
      const cameraStatusRequests = cameraIdxs.map((idx) => {
        return proboter.getCameraStatus(idx, true).then((camera) => {
          return camera;
        });
      });
      Promise.all(cameraStatusRequests).then((cameras) => {
        this.movableCameras = cameras;
      });
    },

    /***************************************
     *
     * Light controller actions
     *
     ***************************************/
    async syncLightControllerStatus() {
      proboter.getLightStatus().then((light) => {
        this.light = light;
      });
    },

    async setLight(on: boolean) {
      return proboter.switchLight(on).then((newLight) => {
        this.light = newLight;
      });
    },

    /***************************************
     *
     * Target power controller actions
     *
     ***************************************/
    async syncTargetPowerControllerStatus() {
      proboter.getPowerState().then((power) => {
        this.power = power;
      });
    },

    async setPower(on: boolean) {
      log.info("[ProboterStore] setPower", on);
      return proboter.switchPower(on).then((newPower) => {
        this.power = newPower;
      });
    },

    /***************************************
     *
     * Signal multiplexer actions
     *
     ***************************************/
    syncSignalMultiplexer() {
      proboter.getMultiplexerStatus().then((status) => {
        this.signalMultiplexer = status;
      });
    },

    async switchDigital(channel: number) {
      console.log("Requesting switch to digital");
      return proboter.switchDigital(channel).then((multiplexer) => {
        this.signalMultiplexer = multiplexer;
      });
    },

    async switchAnalog(channel: number) {
      console.log("Requesting switch to analog");
      return proboter.connectChannelToAnalog(channel).then((multiplexer) => {
        this.signalMultiplexer = multiplexer;
      });
    },

    async pullChannel(channel: number) {
      console.log("Requesting pull of channel");
      return proboter.pullChannel(channel).then((multiplexer) => {
        this.signalMultiplexer = multiplexer;
      });
    },

    async releaseChannel(channel: number) {
      console.log("Requesting release of channel");
      return proboter.releaseChannel(channel).then((multiplexer) => {
        this.signalMultiplexer = multiplexer;
      });
    },

    async updateProbeConfiguration(probe: Probe, config: ProbeConfig) {
      return proboter.updateProbeConfig(probe, config);
    },

    async updateStaticCameraConfiguration(
      camera: Camera,
      config: StaticCameraConfig
    ): Promise<StaticCameraConfig> {
      return proboter
        .updateStaticCameraConfig(camera, config)
        .then((newConfig) => {
          return newConfig;
        });
    },

    /***************************************
     *
     * Task actions
     *
     ***************************************/
    async syncProboterCurrentTask() {
      return proboter.taskGetCurrent().then((currentTask) => {
        this.currentTask = currentTask;
      });
    },

    async cancelCurrentTask() {
      return proboter.taskCancelCurrent();
    },
  },
});
