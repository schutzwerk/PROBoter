<script setup lang="ts">
/**
 * Component to create a new PCB scan
 */
import { reactive, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import BaseButton from "@/components/base/BaseButton.vue";
import BaseForm from "@/components/base/BaseForm.vue";
import BaseFormGroup from "@/components/base/BaseFormGroup.vue";
import BaseFormSelect from "@/components/base/BaseFormSelect.vue";
import BaseFormInput from "@/components/base/BaseFormInput.vue";
import BaseNavigationContainer from "@/components/base/BaseNavigationContainer.vue";
import BaseInputVector2D from "@/components/base/BaseInputVector2D.vue";
import BaseProgressOverlay from "@/components/base/BaseProgressOverlay.vue";
import type { PcbScanParameters, Camera, Pcb } from "@/models";
import { usePcbStore } from "@/stores/pcbs";
import { useProboterStore } from "@/stores/proboter";
import { proboter } from "@/api";
import log from "js-vue-logger";

const router = useRouter();
const pcbs = usePcbStore();
const proboterStore = useProboterStore();

const props = defineProps({
  pcbId: {
    type: Number,
    required: true,
  },
});

interface State {
  scanParameters: PcbScanParameters;
  camera: Camera | null;
  pcbThickness: number;
  errorMsg: string | null;
  busy: boolean;
  statusText: string;
}

const state: State = reactive({
  scanParameters: {
    name: "",
    pcbId: -1,
    xRange: [-150, 150],
    yRange: [-100, 100],
    zOffset: 0,
    imageResolution: [1920, 1080],
  },
  camera: null,
  pcbThickness: 2.0,
  errorMsg: null,
  busy: false,
  statusText: "",
});

const cameraItems = computed(() => {
  // Static camera items only at the moment!
  let items = proboterStore.staticCameras.map((camera) => {
    return {
      text: camera.name,
      value: camera,
    };
  });
  return items;
});

const hasError = computed(() => {
  return state.errorMsg != null;
});

onMounted(() => {
  if (cameraItems.value.length > 0) {
    // Select the first camera by default
    state.camera = cameraItems.value[0].value;
  }
  // Set default scan name
  state.scanParameters.name = "Scan " + new Date().toLocaleDateString();
});

function createScan() {
  /**
   * Trigger PCB scan
   */
  if (!state.camera) {
    log.error("No camera selected");
    return;
  }

  let pcb = pcbs.getPcbById(props.pcbId);
  if (!pcb) {
    log.error("PCB not found");
    return;
  }

  state.scanParameters.pcbId = pcb.id;
  state.scanParameters.zOffset = -state.pcbThickness * 0.5;

  state.errorMsg = null;
  log.debug("Creating new PCB scan with parameters:", state.scanParameters);
  state.statusText = "Scanning PCB...";
  state.busy = true;
  proboter
    .createPcbScanWithStaticCamera(state.camera, state.scanParameters)
    .then((scanResult) => {
      log.debug("Created new scan:", scanResult);
      pcbs.syncPcbScans(pcb as Pcb);
      emit("scan:created", scanResult.scan);
      router.replace({ name: "pcb-detail" });
    })
    .finally(() => {
      state.busy = false;
      state.statusText = "";
    });
}

const emit = defineEmits(["scan:created"]);
</script>

<template>
  <base-navigation-container title="Scan PCB" :to="{ name: 'pcb-detail' }">
    <base-progress-overlay
      :show="state.busy"
      :text="state.statusText"
      class="dp-08"
    >
      <base-form>
        <div class="row">
          <div class="col">
            <!-- Scan Name -->
            <base-form-group
              label="Scan name:"
              label-for="input-scan-name"
              description="Name of the new scan"
            >
              <base-form-input
                id="input-scan-name"
                v-model="state.scanParameters.name"
                type="text"
                placeholder="Scan name"
                required
              />
            </base-form-group>

            <!-- Cameras -->
            <base-form-group
              label="Camera:"
              label-for="input-camera"
              description="Movable camera to use for scan"
            >
              <base-form-select
                v-model="state.camera"
                :options="cameraItems"
                required
              />
            </base-form-group>

            <!-- Scan range X -->
            <base-form-group
              label="Scan X"
              label-for="input-x-range"
              description="X scan range"
            >
              <base-input-vector2-d
                id="input-x-range"
                v-model="state.scanParameters.xRange"
                required
              />
            </base-form-group>

            <!-- Scan range Y -->
            <base-form-group
              label="Scan Y"
              label-for="input-y-range"
              description="Y scan range"
            >
              <base-input-vector2-d
                id="input-y-range"
                v-model="state.scanParameters.yRange"
                required
              />
            </base-form-group>

            <!-- PCB thickness / Z offset -->
            <base-form-group
              label="PCB thickness:"
              label-for="input-pcb-thickness"
              description="PCB thickness in mm"
            >
              <base-form-input
                id="input-pcb-thickness"
                v-model="state.pcbThickness"
                type="number"
                required
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
                :disabled="state.busy"
                @click="createScan"
              >
                <span v-if="state.busy">Scanning...</span>
                <span v-else>Create</span>
              </base-button>
            </div>
          </div>
        </div>

        <div class="row">
          <div class="col">
            <!-- Display calibration errors -->
            <div v-if="hasError" class="alert alert-danger mt-2">
              {{ state.errorMsg }}
            </div>
          </div>
        </div>
      </base-form>
    </base-progress-overlay>
  </base-navigation-container>
</template>
