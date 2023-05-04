<script setup lang="ts">
/**
 * Component to configure the settings of a single static camera system
 */

import { reactive, computed, onMounted } from "vue";
import Vector2DInput from "@/components/base/BaseInputVector2D.vue";
import { proboter } from "@/api";
import { useProboterStore } from "@/stores/proboter";
import type { Matrix4x4, StaticCameraConfig } from "@/models";
import BaseButton from "@/components/base/BaseButton.vue";
import BaseFormGroup from "../base/BaseFormGroup.vue";
import BaseInputMatrix2D from "../base/BaseInputMatrix2D.vue";
import log from "js-vue-logger";

const props = defineProps({
  /**
   * Index of the static camera to configure
   */
  cameraIndex: {
    type: Number,
    required: true,
  },
});

const proboterStore = useProboterStore();

interface State {
  errorMsg: string | null;
  name: string;
  usbDeviceName: string;
  resolution: [number, number];
  tmatToGlob: Matrix4x4;
  config: StaticCameraConfig | null;
}

const state: State = reactive({
  errorMsg: null,
  name: "",
  usbDeviceName: "",
  resolution: [-1, -1],
  tmatToGlob: [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
  ],
  config: null,
});

const hasError = computed(() => state.errorMsg != null);

const emit = defineEmits(["saved"]);

onMounted(() => {
  proboterStore.fetchStaticCameraByIndex(props.cameraIndex).then((camera) => {
    if (camera) {
      proboter.getStaticCameraConfig(camera).then((cameraConfig) => {
        state.config = cameraConfig;
        state.name = cameraConfig.name;
        state.usbDeviceName = cameraConfig.usbDeviceName;
        state.resolution = cameraConfig.resolution;
        state.tmatToGlob = cameraConfig.tmatToGlobal;
      });
    }
  });
});

function submitConfiguration() {
  let newConfig: StaticCameraConfig = JSON.parse(JSON.stringify(state.config));
  newConfig.name = state.name;
  newConfig.usbDeviceName = state.usbDeviceName;
  newConfig.resolution = state.resolution;
  newConfig.tmatToGlobal = state.tmatToGlob;

  state.errorMsg = null;
  proboterStore.fetchStaticCameraByIndex(props.cameraIndex).then((camera) => {
    if (camera) {
      proboter
        .updateStaticCameraConfig(camera, newConfig)
        .then(() => {
          log.debug("Camera config updated successfully");
          emit("saved");
        })
        .catch((error) => {
          state.errorMsg = "Error: " + error.message;
          log.error("Failed to save calibration data: " + state.errorMsg);
        });
    }
  });
}
</script>

<template>
  <form>
    <!-- Camera Name -->
    <div class="row mb-3">
      <div class="col">
        <label for="input-camera-name" class="form-label">Name</label>
        <input
          id="input-camera-name"
          v-model="state.name"
          type="text"
          class="form-control"
          required
        />
      </div>
    </div>

    <!-- USB device name -->
    <div class="row mb-3">
      <div class="col">
        <label for="input-usb-device-name" class="form-label">USB device</label>
        <input
          id="input-usb-device-name"
          v-model="state.usbDeviceName"
          type="text"
          class="form-control"
          required
        />
      </div>
    </div>

    <!-- Camera resolution -->
    <div class="row mb-3">
      <div class="col">
        <Vector2DInput
          id="input-resolution"
          v-model="state.resolution"
          label="Camera resolution"
          x-label="Width"
          y-label="Height"
          required
        />
      </div>
    </div>

    <!-- Probe local to global transformation matrix-->
    <div class="row mb-3">
      <div class="col">
        <base-form-group
          label="Tmat. local -> global"
          description="4x4 transformation matrix from the camera's local to the PROBoter's global coordinate system"
        >
          <base-input-matrix2-d
            v-model="state.tmatToGlob"
            :dimension="[4, 4]"
            :rows="7"
          />
        </base-form-group>
      </div>
    </div>

    <div class="row">
      <div class="col">
        <div class="d-flex justify-content-center">
          <base-button
            class="mr-2"
            variant="primary"
            @click="submitConfiguration"
          >
            Save
          </base-button>
        </div>
      </div>
    </div>

    <div class="row mt-3">
      <div class="col">
        <!-- Display calibration errors -->
        <div v-if="hasError" class="alert alert-danter">
          {{ state.errorMsg }}
        </div>
      </div>
    </div>
  </form>
</template>
