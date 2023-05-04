<script setup lang="ts">
/**
 * Component to calibrate a single static camera system
 */
import { reactive, computed, onMounted } from "vue";

import { saveAs } from "file-saver";
import log from "js-vue-logger";

import type {
  ReferenceBoard,
  StaticCameraCalibrationConfig,
  StaticCameraCalibrationResult,
} from "@/models";
import { proboter } from "@/api";
import { useProboterStore } from "@/stores/proboter";
import CameraFeedView from "@/components/proboter/ProboterCameraFeedView.vue";
import BaseButton from "@/components/base/BaseButton.vue";
import BaseFormGroup from "@/components/base/BaseFormGroup.vue";
import BaseTable from "@/components/base/BaseTable.vue";
import type { TableField } from "@/components/base/BaseTable.vue";
import BaseFormSelect from "@/components/base/BaseFormSelect.vue";
import BaseFormInput from "@/components/base/BaseFormInput.vue";

const props = defineProps({
  cameraIndex: {
    type: Number,
    required: true,
  },
});

const proboterStore = useProboterStore();

interface State {
  defaultCalibrationConfig: StaticCameraCalibrationConfig | null;
  numCalibrationRuns: string;
  refBoards: Array<ReferenceBoard>;
  selectedRefBoard: ReferenceBoard | null;
  brightnessThreshold: number;
  errorMsg: string | null;
  result: Array<StaticCameraCalibrationResult>;
  resultFields: Array<TableField>;
}

const state: State = reactive({
  defaultCalibrationConfig: null,
  numCalibrationRuns: "1",
  refBoards: [],
  selectedRefBoard: null,
  errorMsg: null,
  result: [],
  resultFields: [
    { key: "idx", label: "Run" },
    { key: "u", label: "ΔX in pixel" },
    { key: "v", label: "ΔY in pixel" },
    { key: "x", label: "ΔX in mm" },
    { key: "y", label: "ΔY in mm" },
  ],
  brightnessThreshold: 0,
});

const hasError = computed(() => {
  return state.errorMsg != null;
});

const referenceBoardItems = computed(() => {
  return state.refBoards.map((board) => ({
    value: board,
    text: board.name,
  }));
});

const calibrationResults = computed(() => {
  //result.max_residuals_local_to_global
  return state.result.map((res, idx) => ({
    idx: idx + 1,
    u: res.maxResidualsGlobalToLocal[0].toPrecision(3),
    v: res.maxResidualsGlobalToLocal[1].toPrecision(3),
    x: res.maxResidualsImageToGlobal[0].toPrecision(3),
    y: res.maxResidualsImageToGlobal[1].toPrecision(3),
  }));
});

onMounted(() => {
  // Fetch all defined reference boards
  proboter.getReferenceBoards().then((refBoards) => {
    state.refBoards = refBoards;
    state.selectedRefBoard = refBoards[0];
  });

  // Fetch the default calibration config
  proboterStore.fetchStaticCameraByIndex(props.cameraIndex).then((camera) => {
    if (camera) {
      proboter.getStaticCameraCalibrationConfig(camera).then((config) => {
        state.defaultCalibrationConfig = config;
        state.brightnessThreshold = config.brightnessThreshold;
      });
    }
  });
});

function calibrate() {
  /**
   * Tirgger the calibration of the probe with the defined settings
   */
  if (!state.selectedRefBoard) {
    log.error("No reference board selected");
    return;
  }

  if (!state.defaultCalibrationConfig) {
    log.error("Default calibration config not loaded");
    return;
  }

  state.errorMsg = null;
  log.info("Calibrating static camera " + props.cameraIndex);

  proboterStore
    .fetchStaticCameraByIndex(props.cameraIndex)
    .then((camera) => {
      if (camera && state.selectedRefBoard && state.defaultCalibrationConfig) {
        return proboter.calibrateStaticCamera(
          camera,
          state.selectedRefBoard.id,
          state.brightnessThreshold,
          state.defaultCalibrationConfig.imageResolution,
          Number.parseInt(state.numCalibrationRuns)
        );
      }
    })
    .then((calibrationResults) => {
      log.info("Calibration finished:", calibrationResults);
      if (calibrationResults) {
        state.result = calibrationResults;
      }
    })
    .catch((error) => {
      state.errorMsg = "Error: " + error.message;
      log.error("Failed to calibrate camera system: ", state.errorMsg);
    });
}

function saveAsNewDefault() {
  /**
   * Save the current calibrations as new defaults for the
   * current static camera at the PROBoter server
   */
  if (!state.defaultCalibrationConfig) return;

  // Update the calibration config
  state.defaultCalibrationConfig.brightnessThreshold =
    state.brightnessThreshold;
  log.debug(
    "Saving calibration data as new default",
    state.defaultCalibrationConfig
  );
  proboterStore
    .fetchStaticCameraByIndex(props.cameraIndex)
    .then((camera) => {
      if (camera && state.defaultCalibrationConfig) {
        return proboter.updateStaticCameraCalibrationConfig(
          camera,
          state.defaultCalibrationConfig
        );
      }
    })
    .then(() => {
      log.info("Successfully updated camera calibration defaults");
    })
    .catch((error) => {
      state.errorMsg = "Error: " + error.message;
      log.error("Failed to save calibration data: " + state.errorMsg);
    });
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
   * Permanently store the new camera configuration
   * at the PROBoter server
   */
  if (state.result.length < 1) {
    log.error("No calibration results");
    return;
  }

  log.info("Updating static camera config");
  proboterStore
    .fetchStaticCameraByIndex(props.cameraIndex)
    .then((camera) => {
      if (camera) {
        return proboter.getStaticCameraConfig(camera).then((config) => {
          config.tmatToGlobal = state.result[0].tmat;
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
        "Error while updating static camera configuration: ",
        state.errorMsg
      );
    });
}

function clearResults() {
  /**
   * Clear the calibration results
   */
  state.result = [];
  state.errorMsg = null;
}
</script>

<template>
  <div>
    <div class="row">
      <div class="col">
        <form>
          <div class="row mb-4">
            <div class="col" md="6">
              <!-- Reference board -->
              <base-form-group
                label="Reference board:"
                label-for="input-reference-board"
                description="Reference board to use"
              >
                <base-form-select
                  v-model="state.selectedRefBoard"
                  :options="referenceBoardItems"
                  required
                />
              </base-form-group>

              <!-- Brightness threshold-->
              <base-form-group
                label="Brightness threshold"
                description="Brightness threshold in the range of [0,255]"
                label-for="input-brightness-threshold"
              >
                <base-form-input
                  id="input-brightness-threshold"
                  v-model="state.brightnessThreshold"
                  type="number"
                  required
                />
              </base-form-group>

              <!-- Number of calibration runs -->
              <base-form-group
                label="Number of calibration runs"
                label-for="input-num-runs"
              >
                <base-form-input
                  id="input-num-runs"
                  v-model="state.numCalibrationRuns"
                  type="number"
                  min="1"
                  max="100"
                  required
                />
              </base-form-group>
            </div>

            <div class="col" md="6">
              <!-- Camera live feed -->
              <camera-feed-view :camera-index="props.cameraIndex" />
            </div>
          </div>

          <div class="row">
            <div class="col">
              <div class="d-flex justify-content-center">
                <base-button
                  class="me-2"
                  variant="primary"
                  title="Run the calibration"
                  @click="calibrate"
                >
                  Calibrate
                </base-button>

                <base-button
                  variant="secondary"
                  title="Save the current settings as calibration defaults"
                  @click="saveAsNewDefault"
                >
                  Save as Default
                </base-button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>

    <div class="row">
      <div class="col">
        <!-- Display calibration errors -->
        <div v-if="hasError" class="alert alert-danger mt-2" variant="danger">
          {{ state.errorMsg }}
        </div>

        <!-- Display the calibration results -->
        <div v-if="state.result.length > 0" class="mt-3">
          <div class="alert alert-success">
            <div class="container container-fluid">
              <div class="row mb-2">
                <div class="col">
                  <h5>Calibration results</h5>
                </div>
              </div>
              <div class="row">
                <div class="col">
                  <base-table
                    striped
                    hover
                    :items="calibrationResults"
                    :fields="state.resultFields"
                  />
                </div>
              </div>
            </div>
          </div>

          <div class="d-flex justify-content-center">
            <base-button
              title="Update the probe configuration with the calibration results"
              variant="primary"
              class="me-2"
              @click="applyResults"
            >
              Apply
            </base-button>

            <base-button
              title="Download calibration results"
              variant="secondary"
              class="me-2"
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
