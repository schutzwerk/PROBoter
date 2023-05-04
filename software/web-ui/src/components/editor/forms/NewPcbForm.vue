<script setup lang="ts">
/**
 * Component to create a single PCB
 */
import { reactive, computed } from "vue";
import log from "js-vue-logger";
import { usePcbStore } from "@/stores/pcbs";

import BaseForm from "@/components/base/BaseForm.vue";
import BaseFormGroup from "@/components/base/BaseFormGroup.vue";
import BaseFormInput from "@/components/base/BaseFormInput.vue";

const emit = defineEmits(["pcbCreated"]);

const store = usePcbStore();

interface RootState {
  pcbConfig: {
    name: string;
    description: string;
    thickness: number;
  };
  errorMsg: string | null;
}

const state = reactive({
  pcbConfig: {
    name: "PCB",
    description: "",
    thickness: 2.0,
  },
  errorMsg: null,
} as RootState);

const hasError = computed(() => {
  return state.errorMsg != null;
});

function createPcb(event: MouseEvent) {
  /**
   * Create a new PCB
   */
  store
    .createPcb(
      state.pcbConfig.name,
      state.pcbConfig.description,
      state.pcbConfig.thickness
    )
    .then((newPcb) => {
      log.debug("Created new PCB: " + newPcb.id);
      clearResults();
      emit("pcbCreated", newPcb);
    })
    .catch((error) => {
      console.log(error);
      state.errorMsg = "Error: " + error.response.data.message;
      log.error("Failed to create PCB: " + state.errorMsg);
    });
  event.preventDefault();
  return false;
}

function clearResults() {
  /**
   * Clear error
   */
  state.pcbConfig.name = "";
  state.pcbConfig.description = "";
  state.errorMsg = null;
}
</script>

<template>
  <div>
    <base-form>
      <!-- PCB Name -->
      <base-form-group for="input-pcb-name" label="Name" description="PCB name">
        <base-form-input
          id="input-pcb-name"
          v-model="state.pcbConfig.name"
          type="text"
          required
        />
      </base-form-group>

      <!-- PCB Thickness -->
      <base-form-group
        for="input-pcb-thickness"
        label="Thickness"
        description="PCB thickness in mm"
      >
        <base-form-input
          id="input-pcb-thickness"
          v-model="state.pcbConfig.thickness"
          type="number"
        />
      </base-form-group>

      <!-- PCB Description -->
      <base-form-group
        for="input-pcb-description"
        label="Description"
        description="PCB description or additional notes"
      >
        <textarea
          id="input-pcb-description"
          v-model="state.pcbConfig.description"
          class="form-control"
        />
      </base-form-group>

      <template #footer>
        <div class="row">
          <div class="col">
            <div class="d-flex justify-content-center">
              <button
                class="btn btn-primary mr-2"
                title="Create the PCB"
                @click="createPcb"
              >
                Create
              </button>
            </div>
          </div>
        </div>

        <div v-if="hasError" class="row">
          <div class="col">
            <!-- Display calibration errors -->
            <div class="alert alert-danger mt-2">{{ state.errorMsg }}</div>
          </div>
        </div>
      </template>
    </base-form>
  </div>
</template>
