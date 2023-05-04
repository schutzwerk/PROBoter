<script setup lang="ts">
/**
 * Component to calibrate a single static camera system
 */
import { reactive, computed } from "vue";

import log from "js-vue-logger";
import { saveAs } from "file-saver";

import { proboter } from "@/api";
import { useProboterStore } from "@/stores/proboter";
import type { CameraIntrinsicsCalibrationResult } from "@/models";

import { BIconTrash } from "bootstrap-icons-vue";
import CameraFeedView from "@/components/proboter/ProboterCameraFeedView.vue";
import BaseInputVector2D from "@/components/base/BaseInputVector2D.vue";
import BaseButton from "@/components/base/BaseButton.vue";

const props = defineProps({
  cameraIndex: {
    type: Number,
    required: true,
  },
});

const proboterStore = useProboterStore();

interface State {
  busy: boolean;
  snapshots: Array<string>;
  gridSize: [number, number];
  fieldSize: [number, number];
  errorMsg: string | null;
  result: CameraIntrinsicsCalibrationResult | null;
}

const state: State = reactive({
  busy: false,
  snapshots: [],
  gridSize: [10, 6],
  fieldSize: [17.73, 18.14],
  errorMsg: null,
  result: null,
});

const hasError = computed(() => {
  return state.errorMsg != null;
});

function takeSnapshot() {
  state.busy = true;
  log.info("Taking snapshot");
  proboterStore
    .fetchStaticCameraByIndex(props.cameraIndex)
    .then((camera) => {
      if (camera) {
        return proboter.takeStaticCameraSnapshot(camera);
      }
    })
    .then((data) => {
      if (data) {
        state.snapshots.push(data);
      }
    })
    .finally(() => {
      state.busy = false;
    });
}

function deleteSnapshot(snapshotIndex: number) {
  state.snapshots.splice(snapshotIndex, 1);
}

function calibrate() {
  state.busy = true;
  state.result = null;
  state.errorMsg = null;

  log.info("Calibrating static camera " + props.cameraIndex);
  let snapshots = state.snapshots.map((snapshot, idx) =>
    dataURLtoFile(snapshot, "snapshot-" + idx + ".png")
  );
  proboterStore
    .fetchStaticCameraByIndex(props.cameraIndex)
    .then((camera) => {
      if (camera) {
        return proboter.calibrateStaticCameraIntrinsicParameters(
          camera,
          false,
          snapshots,
          state.gridSize,
          state.fieldSize
        );
      }
    })
    .then((calibrationResults) => {
      log.info("Calibration finished:");
      log.info(calibrationResults);
      if (calibrationResults) {
        state.result = calibrationResults;
      }
    })
    .catch((error) => {
      state.errorMsg = "Error: " + error.message;
      log.error("Failed to calibrate camera system: " + state.errorMsg);
    })
    .finally(() => {
      state.busy = false;
    });
}

function dataURLtoFile(dataurl: string, filename: string): File {
  var arr = dataurl.split(",");
  var mime = "image/png";
  if (arr.length > 0) {
    var mime_match = arr[0].match(/:(.*?);/);
    if (mime_match) {
      mime = mime_match[1];
    }
  }
  var bstr = atob(arr[1]);
  var n = bstr.length;
  var u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new File([u8arr], filename, { type: mime });
}

function downloadResults() {
  /**
   * Present the user a download dialog to locally
   * save the calibration results
   */
  log.info("Start download of calibration results");
  // Convert the result data to a JSON plain text file
  var resultBlob = new Blob([JSON.stringify(state.result, null, 2)], {
    type: "text/plain;charset=utf-8",
  });
  saveAs(
    resultBlob,
    "static_camera_" + props.cameraIndex + "_calibration.json"
  );
}

function applyResults() {
  /**
   * Permanently store the new camera parameters
   * at the PROBoter server
   */
  if (!state.result) {
    log.error("No calibration results available");
    return;
  }

  // Update static camera
  log.info("Applying new camera configuration");
  proboterStore
    .fetchStaticCameraByIndex(props.cameraIndex)
    .then((camera) => {
      if (camera) {
        return proboter.getStaticCameraConfig(camera).then((config) => {
          if (!state.result) return;
          config.cameraMatrix = state.result.cameraMatrix;
          config.distCoefficients = state.result.distortionCoefficients;
          return proboter.updateStaticCameraConfig(camera, config);
        });
      }
    })
    .then(() => {
      log.info("Successfully updated static camera configuration");
    })
    .catch((error) => {
      state.errorMsg = "Error: " + error.message;
      log.error(
        "Error while applying new static camera configuration: " +
          state.errorMsg
      );
    });
}

function clearResults() {
  /**
   * Clear the calibration results
   */
  state.result = null;
  state.errorMsg = null;
}
</script>

<template>
  <div class="container">
    <!-- Form-->
    <div class="row mb-4">
      <div class="col">
        <form>
          <div class="row">
            <!-- Snapshot list -->
            <div class="col-md-6">
              <label class="form-label">Snapshots</label>
              <div class="snapshot-list dp-24">
                <div
                  v-for="(snapshot, idx) of state.snapshots"
                  :key="idx"
                  class="row mb-2"
                >
                  <div class="col-sm-10">
                    <img style="max-width: 100%" :src="snapshot" />
                  </div>
                  <div class="col-sm-2">
                    <base-button
                      variant="danger"
                      title="Delete snapshot"
                      @click="deleteSnapshot(idx)"
                      ><b-icon-trash />
                    </base-button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Camera live feed and other options -->
            <div class="col-md-6">
              <!-- Camera feed -->
              <div class="row mb-3">
                <div class="col">
                  <label class="form-label">Camera feed</label>
                  <camera-feed-view :camera-index="props.cameraIndex" />
                </div>
              </div>
              <!-- Button to create new snapshots -->
              <div class="row mb-3">
                <div class="col">
                  <div class="d-flex justify-content-center mt-2">
                    <base-button class="align-center" @click="takeSnapshot"
                      >Take snapshot</base-button
                    >
                  </div>
                </div>
              </div>

              <div class="row mb-3">
                <div class="col">
                  <BaseInputVector2D
                    v-model="state.gridSize"
                    label="Grid size"
                  />
                </div>
              </div>
              <div class="row mb-3">
                <div class="col">
                  <BaseInputVector2D
                    v-model="state.fieldSize"
                    label="Field size"
                  />
                </div>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>

    <!-- Main Controls-->
    <div class="row">
      <div class="col">
        <div class="d-flex justify-content-center">
          <base-button
            variant="primary"
            title="Run the calibration"
            @click="calibrate"
          >
            Calibrate
          </base-button>
        </div>
      </div>
    </div>

    <!-- Status messages -->
    <div class="row mt-4">
      <!-- Error message-->
      <div v-if="hasError" class="alert alert-danger">
        {{ state.errorMsg }}
      </div>
    </div>

    <!--Calibration results-->
    <div v-if="state.result">
      <div class="row">
        <div class="col">
          <div class="alert alert-success">
            <h5>Calibration results</h5>
          </div>
        </div>
      </div>

      <div class="row">
        <div class="col">
          <div class="d-flex justify-content-center">
            <base-button
              title="Update the probe configuration with the calibration results"
              variant="primary"
              class="mr-2"
              @click="applyResults"
            >
              Apply
            </base-button>

            <base-button
              title="Download calibration results"
              variant="secondary"
              class="mr-2"
              @click="downloadResults"
            >
              Download
            </base-button>

            <base-button
              title="Clear the calibration results"
              variant="danger"
              @click="clearResults"
            >
              Clear
            </base-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="css">
.snapshot-list {
  height: 700px;
  overflow-y: "auto";
}
</style>
