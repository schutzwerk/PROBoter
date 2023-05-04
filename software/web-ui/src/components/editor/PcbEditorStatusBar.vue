<script setup lang="ts">
/*
 * Simple status bar to display messages to the user
 */
import { usePcbEditorStore } from "@/stores/pcbEditor";
import BaseButton from "@/components/base/BaseButton.vue";
import { BIconCheckLg } from "bootstrap-icons-vue";

const store = usePcbEditorStore();
</script>

<template>
  <div v-if="store.statusBar.text" class="pcb-editor-status-bar">
    <span class="pcb-editor-status-bar-text dp-24">{{
      store.statusBar.text
    }}</span>
    <div class="pcb-editor-status-bar-buttons">
      <base-button
        v-for="(btn, idx) in store.statusBar.buttons"
        :key="idx"
        class="pcb-editor-status-bar-button"
        :variant="btn.variant"
        @click="btn.action()"
      >
        <b-icon-check-lg v-if="btn.icon == 'commit'" />
        <span v-else-if="btn.icon == 'cancel'">X</span>
        <span v-else>{{ btn.text }}</span>
      </base-button>
    </div>
  </div>
</template>

<style scoped>
.pcb-editor-status-bar {
  display: flex;
}

.pcb-editor-status-bar-button {
  border-radius: 0;
}

.pcb-editor-status-bar-button:last-of-type {
  border-radius: 0 0.25em 0.25rem 0;
}

.pcb-editor-status-bar-text {
  padding: 0.375em 0.75em;
  border-width: 1px;
  border-radius: 0.25em 0 0 0.25rem;
  float: left;
}
</style>
