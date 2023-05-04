<script setup lang="ts">
/**
 * Component to view and change the configuration of a
 * single electrical probing unit
 */

import { reactive, computed, onMounted } from "vue";
import type { PropType } from "vue";
import BaseForm from "@/components/base/BaseForm.vue";
import BaseButton from "@/components/base/BaseButton.vue";
import BaseAlert from "@/components/base/BaseAlert.vue";
import BaseFormGroup from "@/components/base/BaseFormGroup.vue";
import BaseFormInput from "@/components/base/BaseFormInput.vue";
import BaseInputVector3D from "@/components/base/BaseInputVector3D.vue";
import BaseInputMatrix2D from "../base/BaseInputMatrix2D.vue";
import type { Matrix4x4, ProbeType, ProbeConfig, Vector3D } from "@/models";
import { useProboterStore } from "@/stores/proboter";
import { proboter } from "@/api";
import log from "js-vue-logger";

const proboterStore = useProboterStore();

const props = defineProps({
  probeType: {
    type: String as PropType<ProbeType>,
    required: true,
  },
});

const emit = defineEmits(["saved"]);

interface State {
  errorMsg: string | null;
  name: string;
  posXSafetyPosition: Vector3D;
  negXSafetyPosition: Vector3D;
  tmatToGlob: Matrix4x4;
  probeConfig: ProbeConfig | null;
}

const state: State = reactive({
  errorMsg: null,
  name: "",
  posXSafetyPosition: [0, 0, 0],
  negXSafetyPosition: [0, 0, 0],
  tmatToGlob: [
    [1, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1],
  ],
  probeConfig: null,
});

const hasError = computed(() => {
  return state.errorMsg != null;
});

onMounted(() => {
  proboterStore.fetchProbeByType(props.probeType).then((probe) => {
    if (probe) {
      proboter.getProbeConfig(probe).then((config) => {
        log.debug("Fetching config of probe " + probe.probeType);
        state.probeConfig = config;
        state.name = config.name;
        state.posXSafetyPosition = config.posXSafetyPosition;
        state.negXSafetyPosition = config.negXSafetyPosition;
        state.tmatToGlob = config.tmatToGlob;
      });
    }
  });
});

function submitConfiguration() {
  state.errorMsg = null;
  if (state.probeConfig) {
    log.info("Updating configuration of probe " + props.probeType);
    state.probeConfig.name = state.name;
    state.probeConfig.posXSafetyPosition = state.posXSafetyPosition;
    state.probeConfig.negXSafetyPosition = state.negXSafetyPosition;
    state.probeConfig.tmatToGlob = state.tmatToGlob;
    proboterStore.fetchProbeByType(props.probeType).then((probe) => {
      if (probe && state.probeConfig) {
        proboterStore
          .updateProbeConfiguration(probe, state.probeConfig)
          .then(() => {
            log.debug("Successfully updated probe config");
            emit("saved");
          })
          .catch((error) => {
            state.errorMsg = "Error: " + error.response.data.message;
            log.error("Failed to save calibration data: " + state.errorMsg);
          });
      }
    });
  }
}
</script>

<template>
  <base-form>
    <div class="row">
      <div class="col">
        <!-- Probe Name -->
        <base-form-group
          label="Probe name"
          label-for="input-probe-name"
          description="Name of the probe"
        >
          <base-form-input
            id="input-probe-name"
            v-model="state.name"
            type="text"
            required
          />
        </base-form-group>

        <!-- Pos. X safety position -->
        <base-form-group
          label="Pos. X safety position"
          description="Positive safety position in local coordinates"
          label-for="input-pos-x-safety-pos"
        >
          <base-input-vector3-d
            id="input-pos-x-safety-pos"
            v-model="state.posXSafetyPosition"
            required
          />
        </base-form-group>

        <!-- Neg. X safety position -->
        <base-form-group
          label="Neg. X safety position"
          description="Negative safety position in local coordinates"
          label-for="input-neg-x-safety-pos"
        >
          <base-input-vector3-d
            id="input-neg-x-safety-pos"
            v-model="state.negXSafetyPosition"
            required
          />
        </base-form-group>

        <!-- Probe local to global transformation matrix-->
        <base-form-group
          label="Tmat. local -> global"
          description="4x4 transformation matrix from the probe's local to the PROBoter's global coordinate system"
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
            title="Save the configuration"
            @click="submitConfiguration"
          >
            Save
          </base-button>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col">
        <!-- Display Error -->
        <base-alert v-if="hasError" variant="danger" class="mt-2"></base-alert>
        {{ state.errorMsg }}
      </div>
    </div>
  </base-form>
</template>
