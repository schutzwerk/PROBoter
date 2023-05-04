<script setup lang="ts">
/**
 * Component to trigger and visualize the analysis of a scan
 */
import { reactive, computed, onMounted } from "vue";
import BaseForm from "@/components/base/BaseForm.vue";
import BaseFormGroup from "@/components/base//BaseFormGroup.vue";
import BaseButton from "@/components/base//BaseButton.vue";
import BaseFormSelect from "@/components/base/BaseFormSelect.vue";
import BaseNavigationContainer from "@/components/base/BaseNavigationContainer.vue";
import BaseProgressOverlay from "@/components/base/BaseProgressOverlay.vue";
import { usePcbStore } from "@/stores/pcbs";
import { pcbApi, visualAnalysis } from "@/api";
import log from "js-vue-logger";
import type {
  Scan,
  Pcb,
  PinDetector,
  ComponentDetector,
  Vector2D,
  ComponentDetectionResult,
} from "@/models";
import { useRouter } from "vue-router";

const pcbs = usePcbStore();
const router = useRouter();

const props = defineProps({
  pcbId: {
    type: Number,
    required: true,
  },
});

const emit = defineEmits(["analysis-finished"]);

interface State {
  selectedScan: Scan | null;
  pinDetectors: PinDetector[];
  selectedPinDetector: PinDetector | null;
  componentDetectors: ComponentDetector[];
  selectedComponentDetector: ComponentDetector | null;
  runPinDetection: boolean;
  busy: boolean;
  errorMsg: string | null;
}

const state: State = reactive({
  selectedScan: null,
  pinDetectors: [],
  selectedPinDetector: null,
  componentDetectors: [],
  selectedComponentDetector: null,
  runPinDetection: true,
  busy: false,
  errorMsg: null,
});

const currentPcb = computed(() => pcbs.getPcbById(props.pcbId));

const scanItems = computed(() => {
  if (!currentPcb.value) return [];
  return currentPcb.value.scans.map((scan) => {
    return {
      text: scan.name,
      value: scan,
    };
  });
});

const pinDetectorItems = computed(() => {
  return state.pinDetectors.map((detector) => {
    return {
      text: detector.name,
      value: detector,
    };
  });
});

const componentDetectorItems = computed(() => {
  return state.componentDetectors.map((detector) => {
    return {
      text: detector.name,
      value: detector,
    };
  });
});

const hasError = computed(() => {
  return state.errorMsg != null;
});

const selectedScanPreviewUrl = computed(() => {
  return state.selectedScan
    ? pcbApi.getScanPreviewUrl(state.selectedScan)
    : undefined;
});

onMounted(() => {
  // Fetch PCB scans
  if (scanItems.value.length > 0) {
    state.selectedScan = scanItems.value[0].value;
  }

  // Load available pin detectors
  visualAnalysis.getPinDetectors().then((pinDetectors) => {
    state.pinDetectors = pinDetectors;
    if (pinDetectors.length > 0)
      state.selectedPinDetector = state.pinDetectors[0];
  });

  // Load available chip detectors
  visualAnalysis.getChipDetectors().then((componentDetectors) => {
    state.componentDetectors = componentDetectors;
    if (componentDetectors.length > 0)
      state.selectedComponentDetector = state.componentDetectors[0];
  });
});

function analyse() {
  /*
  Trigger PCB image analysis
  */
  if (!state.selectedScan) {
    log.error("No PCB scan selected");
    return;
  }
  if (!state.selectedComponentDetector) {
    log.error("No component detector selected");
    return;
  }
  if (state.runPinDetection && !state.selectedPinDetector) {
    log.error("No pin detector selected");
    return;
  }

  let infoMsg =
    "Running PCB analysis: Component Detector = " +
    state.selectedComponentDetector.name;
  infoMsg += state.runPinDetection
    ? " and Pin Detector = " + state.selectedPinDetector?.name
    : "";
  log.debug(infoMsg);

  state.errorMsg = null;
  state.busy = true;
  let runPinDetection = state.runPinDetection;
  let selectedScan = state.selectedScan;
  let selectedComponentDetector = state.selectedComponentDetector;
  let selectedPinDetector = state.selectedPinDetector;

  log.debug("Loading scan image");
  pcbs
    .loadScanImage(state.selectedScan)
    .then((imageData) => {
      log.debug("Scan image received");
      let image = new File([imageData], "scan-" + selectedScan.id, {
        type: imageData.type,
      });
      return visualAnalysis.analysePcbImage(
        image,
        selectedComponentDetector.id,
        runPinDetection && selectedPinDetector ? selectedPinDetector?.id : null
      );
    })
    .then((analysisResults) => {
      log.debug("PCB scan analyis finished:", analysisResults);
      return Promise.all(
        analysisResults.components.map((component) =>
          createComponentWithPinsFromResult(component)
        )
      );
    })
    .then((results) => {
      state.busy = false;
      log.info(
        "Successfully created " +
          results.length +
          " components and " +
          results
            .map((res) => res.pins.length)
            .reduce((acc, curr) => acc + curr, 0) +
          " pins"
      );
      emit("analysis-finished", {
        success: true,
        components: results.map((res) => res.component),
        pins: results
          .map((res) => res.pins)
          .reduce((acc, curr) => acc.concat(curr), []),
      });
      router.replace({ name: "pcb-detail" });
    })
    .catch((error) => {
      state.errorMsg = error.message;
      log.error("Failed to perform PCB scan analysis: ", error.message);
    })
    .finally(() => {
      state.busy = false;
    });
}

function createComponentWithPinsFromResult(
  component: ComponentDetectionResult
) {
  // TODO Improve error handling here!
  let pcb = pcbs.getPcbById(props.pcbId);
  if (!pcb) throw Error();
  let selectedScan = state.selectedScan;
  if (!selectedScan) throw Error();

  return pcbs
    .createComponent(pcb, {
      id: -1,
      name: "",
      contour: imageToGlobalPoints(selectedScan, component.contour),
      pcbId: pcb.id,
      vendor: "UNKNOWN",
      marking: "UNKNOWN",
      package: "UNKNOWN",
      isVisible: true,
      isTemporary: true,
    })
    .then((newComp) => {
      log.debug("Parsing component pin results:", component.pins);
      return Promise.all(
        component.pins.map((pin) =>
          pcbs
            .createPad(pcb as Pcb, {
              id: -1,
              name: "",
              pcbId: (pcb as Pcb).id,
              componentId: newComp.id,
              center: imageToGlobalPoint(selectedScan as Scan, pin.center),
              networkId: undefined,
              isVisible: true,
              isTemporary: true,
            })
            .then((newPin) => {
              return newPin;
            })
        )
      ).then((createdPins) => {
        return {
          component: newComp,
          pins: createdPins,
        };
      });
    });
}

function imageToGlobalPoints(scan: Scan, points: Vector2D[]) {
  return points.map((point2d) => imageToGlobalPoint(scan, point2d));
}

function imageToGlobalPoint(scan: Scan, point: Vector2D) {
  // TODO Find a better solution to map the component contour
  //      from image to global coordinates.
  return [scan.xMax - point[0] * 0.1, scan.yMax - point[1] * 0.1, 0.0];
}
</script>

<template>
  <base-navigation-container title="Scan Analysis" :to="{ name: 'pcb-detail' }">
    <base-progress-overlay class="dp-08" :show="state.busy">
      <div class="row">
        <div class="col">
          <base-form>
            <!-- Scan -->
            <base-form-group
              label="Scan:"
              label-for="input-scan"
              description="Scan to analyse"
            >
              <base-form-select
                v-model="state.selectedScan"
                :options="scanItems"
                required
              />
            </base-form-group>

            <!-- Selected scan preview -->
            <div class="scan-preview text-center mt-4 mb-4">
              <img :src="selectedScanPreviewUrl" />
            </div>

            <!-- Component Detector-->
            <base-form-group
              label="Component detector:"
              label-for="input-component-detector"
              description="Algorithm for component detection"
            >
              <base-form-select
                v-model="state.selectedComponentDetector"
                :options="componentDetectorItems"
                required
              />
            </base-form-group>

            <!-- Run pin detection -->
            <base-form-group>
              <div class="form-check">
                <input
                  id="pin_detection_checkbox"
                  v-model="state.runPinDetection"
                  name="pin_detection_checkbox"
                  class="form-check-input"
                  type="checkbox"
                />
                <label class="form-check-label">Run pin detection</label>
              </div>
            </base-form-group>

            <!-- Pin Detector-->
            <base-form-group
              v-if="state.runPinDetection"
              label="Pin detector:"
              label-for="input-pin-detector"
              description="Algorithm for pin detection"
            >
              <base-form-select
                v-model="state.selectedPinDetector"
                :options="pinDetectorItems"
                required
              />
            </base-form-group>
          </base-form>
        </div>
      </div>

      <div class="row">
        <div class="col">
          <div class="d-flex justify-content-center">
            <base-button
              class="mr-2"
              variant="primary"
              :disabled="
                state.busy ||
                !(state.selectedComponentDetector && state.selectedScan)
              "
              @click="analyse"
              >Analyse</base-button
            >
          </div>
        </div>
      </div>

      <div class="row">
        <div class="col">
          <!-- Display errors -->
          <div v-if="hasError" class="alert alert-danger mt-2">
            {{ state.errorMsg }}
          </div>
        </div>
      </div>
    </base-progress-overlay>
  </base-navigation-container>
</template>
