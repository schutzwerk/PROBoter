import type { RouteLocation } from "vue-router";
import ProboterProbeSettings from "@/components/proboter/ProboterProbeSettings.vue";
import ProboterProbeCalibration from "@/components/proboter/ProboterProbeCalibration.vue";
import ProboterCameraStaticSettings from "@/components/proboter/ProboterCameraStaticSettings.vue";
import ProboterCameraStaticCalibration from "@/components/proboter/ProboterCameraStaticCalibration.vue";
import ProboterCameraStaticCalibrationIntrinsics from "@/components/proboter/ProboterCameraStaticCalibrationIntrinsics.vue";

export const routes = [
  {
    path: "probe/:probeType/settings",
    name: "probe-settings",
    component: ProboterProbeSettings,
    props: (route: RouteLocation) => ({
      probeType: route.params.probeType,
    }),
    meta: {
      showModal: true,
      modalTitle: (route: RouteLocation) => {
        return "Probe " + route.params.probeType + " - Settings";
      },
    },
  },
  {
    path: "probe/:probeType/calibration",
    name: "probe-calibration",
    component: ProboterProbeCalibration,
    props: (route: RouteLocation) => ({
      probeType: route.params.probeType,
    }),
    meta: {
      showModal: true,
      modalTitle: (route: RouteLocation) => {
        return "Calibrate probe " + route.params.probeType;
      },
    },
  },
  {
    path: "camera/static/:cameraIndex/settings",
    name: "camera-static-settings",
    component: ProboterCameraStaticSettings,
    props: (route: RouteLocation) => ({
      cameraIndex: Number.parseInt(route.params.cameraIndex as string),
    }),
    meta: {
      showModal: true,
      modalTitle: () => {
        return "Camera settings";
      },
    },
  },
  {
    path: "camera/static/:cameraIndex/calibration",
    name: "camera-static-calibration",
    component: ProboterCameraStaticCalibration,
    props: (route: RouteLocation) => ({
      cameraIndex: Number.parseInt(route.params.cameraIndex as string),
    }),
    meta: {
      showModal: true,
      modalTitle: () => {
        return "Static camera calibration";
      },
      modalSize: "xl",
    },
  },
  {
    path: "camera/static/:cameraIndex/calibration-intrinsics",
    name: "camera-static-calibration-intrinsics",
    component: ProboterCameraStaticCalibrationIntrinsics,
    props: (route: RouteLocation) => ({
      cameraIndex: Number.parseInt(route.params.cameraIndex as string),
    }),
    meta: {
      showModal: true,
      modalTitle: () => {
        return "Intrinsics Calibration";
      },
      modalSize: "xl",
    },
  },
];
