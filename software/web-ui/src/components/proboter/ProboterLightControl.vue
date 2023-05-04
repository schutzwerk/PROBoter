<script setup lang="ts">
/**
 * Component to control the PROBoter light
 */
import { computed } from "@vue/reactivity";

import { useProboterStore } from "@/stores/proboter";

import BaseFormCheckbox from "@/components/base/BaseFormCheckbox.vue";
import ProboterEntityContainer from "@/components/proboter/ProboterEntityContainer.vue";
import type { EntityStatus } from "@/components/proboter/ProboterEntityContainer.vue";

const proboterStore = useProboterStore();

const isLightOn = computed({
  get() {
    return proboterStore.light?.on || false;
  },
  set(newValue: boolean) {
    proboterStore.setLight(newValue);
  },
});

const lightStatus = computed<EntityStatus>(() => {
  return {
    title: proboterStore.light?.connected ? "CONNECTED" : "DISCONNECTED",
    variant: proboterStore.light?.connected ? "okay" : "error",
  };
});
</script>

<template>
  <proboter-entity-container title="Light" :status="lightStatus">
    <div class="form-check form-switch">
      <base-form-checkbox id="light-control" v-model="isLightOn" />
      <label for="light-control">{{ isLightOn ? "ON" : "OFF" }}</label>
    </div>
  </proboter-entity-container>
</template>
