<script setup lang="ts">
/**
 * Component to control the PROBoter power state
 */
import { computed } from "vue";
import BaseFormCheckbox from "@/components/base/BaseFormCheckbox.vue";
import ProboterEntityContainer from "@/components/proboter/ProboterEntityContainer.vue";
import type { EntityStatus } from "@/components/proboter/ProboterEntityContainer.vue";
import { useProboterStore } from "@/stores/proboter";

const proboter = useProboterStore();

const isPowerOn = computed({
  get() {
    return proboter.power?.on || false;
  },
  set(newPower: boolean) {
    proboter.setPower(newPower);
  },
});

const powerStatus = computed<EntityStatus>(() => {
  return {
    title: proboter.power?.connected ? "CONNECTED" : "DISCONNECTED",
    variant: proboter.power?.connected ? "okay" : "error",
  };
});
</script>

<template>
  <proboter-entity-container title="Target Power" :status="powerStatus">
    <div class="form-check form-switch">
      <base-form-checkbox id="power-state-button" v-model="isPowerOn" />
      <label class="form-check-label" for="power-state-button">{{
        isPowerOn ? "ON" : "OFF"
      }}</label>
    </div>
  </proboter-entity-container>
</template>
