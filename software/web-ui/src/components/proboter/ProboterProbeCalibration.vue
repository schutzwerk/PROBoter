<script setup lang="ts">
/**
 * Component to calibrate a single electrical probing unit
 */
import { reactive, computed, onMounted } from "vue";
import type { PropType } from "vue";
import { saveAs } from "file-saver";
import log from "js-vue-logger";

import { useProboterStore } from "@/stores/proboter";
import { proboter } from "@/api";
import type {
  ProbeType,
  ProbeCalibrationConfig,
  ReferenceBoard,
  Vector3D,
  ProbeCalibrationResult,
} from "@/models";

import BaseButton from "@/components/base/BaseButton.vue";
import BaseForm from "@/components/base/BaseForm.vue";
import BaseAlert from "@/components/base/BaseAlert.vue";
import BaseFormGroup from "@/components/base/BaseFormGroup.vue";
import BaseFormInput from "@/components/base/BaseFormInput.vue";
import BaseFormSelect from "@/components/base/BaseFormSelect.vue";
import BaseTable from "@/components/base/BaseTable.vue";
import BaseInputVector3D from "@/components/base/BaseInputVector3D.vue";
import BaseProgressOverlay from "../base/BaseProgressOverlay.vue";

import type { TableField } from "@/components/base/BaseTable.vue";

const props = defineProps({
  probeType: {
    type: String as PropType<ProbeType>,
    required: true,
  },
});

const proboterStore = useProboterStore();

interface State {
  feed: number;
  homeBeforeCalibration: boolean;
  numCalibrationRuns: number;
  initialProbePositions: Array<Vector3D>;
  refBoards: Array<ReferenceBoard>;
  selectedRefBoard: ReferenceBoard | null;
  errorMsg: string | null;
  busy: boolean;
  resultFields: Array<TableField>;
  defaultCalibrationConfig: ProbeCalibrationConfig | null;
  result: Array<ProbeCalibrationResult>;
  pinPositions: Array<string>;
}

const state: State = reactive({
  feed: 1000,
  homeBeforeCalibration: true,
  numCalibrationRuns: 1,
  initialProbePositions: [],
  defaultCalibrationConfig: null,
  refBoards: [],
  selectedRefBoard: null,
  errorMsg: null,
  result: [],
  busy: false,
  resultFields: [
    { key: "idx", label: "Run" },
    { key: "x", label: "ΔX in mm" },
    { key: "y", label: "ΔY in mm" },
    { key: "z", label: "ΔZ in mm" },
  ],
  pinPositions: ["Upper Left", "Upper Right", "Lower Left", "Lower Right"],
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
  return state.result.map((res, idx) => ({
    idx: idx + 1,
    x: res.maxResidualsLocalToGlobal[0].toPrecision(3),
    y: res.maxResidualsLocalToGlobal[1].toPrecision(3),
    z: res.maxResidualsLocalToGlobal[2].toPrecision(3),
  }));
});

onMounted(() => {
  // Fetch all defined reference boards
  proboter.getReferenceBoards().then((refBoards) => {
    state.refBoards = refBoards;
    state.selectedRefBoard = refBoards[0];
  });

  // Fetch the stored probe default configuration
  proboterStore.fetchProbeByType(props.probeType).then((probe) => {
    if (probe) {
      proboter.getProbeCalibrationConfig(probe).then((config) => {
        state.defaultCalibrationConfig = config;
        state.homeBeforeCalibration = config.homeBeforeCalibration;
        state.feed = config.calibrationFeed;
        state.initialProbePositions = config.initialProbePositions;
      });
    }
  });
});

function calculatePinPositions() {
  /*
   * Cacluate pin positions based on values of the UPPER LEFT pin
   */
  if (!state.selectedRefBoard) {
    log.error("No reference board selected!");
    return;
  }
  // Upper right pin
  state.initialProbePositions[1] = [
    state.initialProbePositions[0][0] -
      state.selectedRefBoard.innerBrassPinWidth,
    state.initialProbePositions[0][1],
    state.initialProbePositions[0][2],
  ];

  // Lower left pin
  state.initialProbePositions[2] = [
    state.initialProbePositions[0][0],
    state.initialProbePositions[0][1] -
      state.selectedRefBoard.innerBrassPinHeight,
    state.initialProbePositions[0][2],
  ];

  // Lower right pin
  state.initialProbePositions[3] = [
    state.initialProbePositions[0][0] -
      state.selectedRefBoard.innerBrassPinWidth,
    state.initialProbePositions[0][1] -
      state.selectedRefBoard.innerBrassPinHeight,
    state.initialProbePositions[0][2],
  ];
}

function testProbePoint(pointIdx: number) {
  /**
   * Move the current probe to one of the initial probing points
   */
  let probePoint = state.initialProbePositions[pointIdx];
  state.busy = true;
  log.info("Probe point " + pointIdx + " @ [" + probePoint + "]");
  proboterStore
    .fetchProbeByType(props.probeType)
    .then((probe) => {
      if (probe) {
        proboter.moveProbe(probe, probePoint, 1000, false).then(() => {
          log.info("Successfully probed point");
        });
      }
    })
    .catch((error) => {
      state.errorMsg = "Error: " + error.message;
      log.error("Failed to test probing point: " + state.errorMsg);
    })

    .finally(() => {
      state.busy = false;
    });
}

function calibrate() {
  /**
   * Trigger the calibration of the probe with the defined settings
   */
  if (!state.selectedRefBoard) {
    state.errorMsg = "Reference board not selected";
    return;
  }

  state.errorMsg = null;
  log.info("Calibrating probe " + props.probeType);
  state.busy = true;
  proboterStore
    .fetchProbeByType(props.probeType)
    .then((probe) => {
      if (probe && state.selectedRefBoard) {
        return proboter.calibrateProbe(
          probe,
          state.selectedRefBoard,
          state.initialProbePositions,
          state.feed,
          state.homeBeforeCalibration,
          state.numCalibrationRuns
        );
      }
    })
    .then((calibrationResults) => {
      log.info("Probe calibration finished:", calibrationResults);
      if (calibrationResults) {
        state.result = calibrationResults;
      }
    })
    .catch((error) => {
      state.errorMsg = "Error: " + error.message;
      log.error("Probe calibration failed: ", error);
    })
    .finally(() => {
      state.busy = false;
    });
}

function saveAsNewDefault() {
  /**
   * Save the current calibrations as new defaults for the
   * current probe at the PROBoter server
   */
  if (!state.defaultCalibrationConfig) {
    return;
  }

  // Update the default calibration config
  state.defaultCalibrationConfig.calibrationFeed = state.feed;
  state.defaultCalibrationConfig.homeBeforeCalibration =
    state.homeBeforeCalibration;
  state.defaultCalibrationConfig.initialProbePositions =
    state.initialProbePositions;

  log.debug(
    "Saving calibration data as new default",
    state.defaultCalibrationConfig
  );
  proboterStore.fetchProbeByType(props.probeType).then((probe) => {
    if (probe && state.defaultCalibrationConfig) {
      proboter
        .updateProbeCalibrationConfig(probe, state.defaultCalibrationConfig)
        .then((newConfig) => {
          log.info("Successfully updated probe calibration defaults");
          state.defaultCalibrationConfig = newConfig;
          state.feed = newConfig.calibrationFeed;
          state.homeBeforeCalibration = newConfig.homeBeforeCalibration;
          state.initialProbePositions = newConfig.initialProbePositions;
        })
        .catch((error) => {
          state.errorMsg = "Error: " + error.message;
          log.error("Failed to save calibration data: " + state.errorMsg);
        });
    }
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
  saveAs(resultBlob, "probe_" + props.probeType + "_calibration.json");
}

function applyResults() {
  /**
   * Permanently store the new probe configuration
   * at the PROBoter server
   */
  log.info("Applying new probe configuration");
  proboterStore.fetchProbeByType(props.probeType).then((probe) => {
    if (probe) {
      proboter
        .getProbeConfig(probe)
        .then((config) => {
          let configUpdate = {
            name: config.name,
            tmatToGlob: state.result[0].tmatLocalToGlobal,
            posXSafetyPosition: config.posXSafetyPosition,
            negXSafetyPosition: config.negXSafetyPosition,
          };
          log.info("Updated config:", configUpdate);
          return proboter.updateProbeConfig(probe, configUpdate);
        })
        .then(() => {
          log.info("Successfully updated probe configuration:");
        })
        .catch((error) => {
          state.errorMsg = "Error: " + error.message;
          log.error(
            "Error while applying new probe configuration: ",
            state.errorMsg
          );
        });
    }
  });
}

function clearResults() {
  state.result = [];
  state.errorMsg = null;
}
</script>

<template>
  <base-progress-overlay :show="state.busy">
    <base-form>
      <!-- Reference board-->
      <base-form-group
        label="Reference board"
        label-for="input-reference-board"
      >
        <base-form-select
          v-model="state.selectedRefBoard"
          :options="referenceBoardItems"
          required
        />
      </base-form-group>

      <!-- Calibration feed -->
      <base-form-group label="Feed" label-for="input-feed">
        <base-form-input
          id="input-feed"
          v-model="state.feed"
          required
          title="Calibration feed in mm/min"
        />
      </base-form-group>

      <!-- Number of calibration runs -->
      <base-form-group label="Calibration runs" label-for="input-num-runs">
        <base-form-input
          id="input-num-runs"
          v-model="state.numCalibrationRuns"
          type="number"
          min="1"
          max="100"
          required
          title="Number of calibration runs"
        />
      </base-form-group>

      <!-- Initial probing positions -->
      <!-- Upper left pin center-->
      <div v-if="state.initialProbePositions.length == 4">
        <base-form-group :label="'Pin: ' + state.pinPositions[0]">
          <BaseInputVector3D
            v-model="state.initialProbePositions[0]"
            @update:model-value="calculatePinPositions()"
          >
            <base-button
              :title="'Move to probe pin ' + state.pinPositions[0]"
              @click="testProbePoint(0)"
            >
              Test
            </base-button>
          </BaseInputVector3D>
        </base-form-group>

        <!-- Remaining / calculated pin centers-->
        <base-form-group
          v-for="(item, index) in state.initialProbePositions.slice(1)"
          :key="index"
          :label="'Pin: ' + state.pinPositions[index + 1]"
        >
          <BaseInputVector3D
            v-model="state.initialProbePositions[index + 1]"
            disabled
          >
            <base-button
              :title="'Move to probe pin ' + state.pinPositions[index + 1]"
              @click="testProbePoint(index + 1)"
            >
              Test
            </base-button>
          </BaseInputVector3D>
        </base-form-group>
      </div>

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
    </base-form>

    <!-- Display calibration errors -->
    <base-alert v-if="hasError" variant="danger" class="mt-2">
      {{ state.errorMsg }}
    </base-alert>

    <!-- Display the calibration results -->
    <div v-if="state.result.length > 0" class="mt-3">
      <base-alert variant="success">
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
      </base-alert>

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
  </base-progress-overlay>
</template>
