<script setup lang="ts">
import { computed } from "vue";
import { usePcbEditorStore } from "@/stores/pcbEditor";

const store = usePcbEditorStore();

const currentPosition = computed(() => {
  if (store.currentProbingPlanePosition) {
    return {
      x: store.currentProbingPlanePosition.x,
      y: store.currentProbingPlanePosition.y,
      z: store.probingPlaneZ,
    };
  } else {
    return {
      x: "?",
      y: "?",
      z: "?",
    };
  }
});

function toPosition(value: string | number) {
  return typeof value === "string" ? value : value.toFixed(2);
}
</script>

<template>
  <div class="pcb-editor-probing-position">
    <div>
      <span class="position-label">X</span>
      <span class="position-value">{{ toPosition(currentPosition.x) }}</span>
    </div>
    <div>
      <span class="position-label">Y</span>
      <span class="position-value">{{ toPosition(currentPosition.y) }}</span>
    </div>
    <div>
      <span class="position-label">Z</span>
      <span class="position-value">{{ toPosition(currentPosition.z) }}</span>
    </div>
  </div>
</template>

<style scoped>
.pcb-editor-probing-position {
  color: white;
  background: rgba(52, 58, 64, 0.9);
  border-radius: 0.25rem;
  display: flex;
  flex-flow: column;
  justify-content: center;
  padding: 10px;
}

.position-label {
  display: inline-block;
}

.position-value {
  display: inline-block;
  width: 60px;
  text-align: right;
}
</style>
