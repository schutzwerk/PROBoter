<script setup lang="ts">
import { reactive, onMounted } from "vue";
import BasePage from "@/components/base/BasePage.vue";
import PcbEditor from "@/components/editor/PcbEditor.vue";
import { usePcbStore } from "@/stores/pcbs";

const store = usePcbStore();

const props = defineProps({
  pcbId: {
    type: Number,
    default: () => null,
  },
});

const state = reactive({
  busy: false,
  pcbName: "PCB - ??",
});

onMounted(() => {
  // Load the PCB data into the global store
  state.busy = true;
  store.fetchPcbById(props.pcbId).then((pcb) => {
    state.pcbName = pcb ? pcb.name : "UNKNOWN";
    state.busy = false;
  });
});
</script>

<template>
  <base-page :title="state.pcbName">
    <!-- PCB editor content -->
    <div class="content-wrapper">
      <!-- Central PCB editor -->
      <pcb-editor v-if="!state.busy" :pcb-id="props.pcbId" class="pcb-editor" />
    </div>
  </base-page>
</template>

<style scoped>
.content-wrapper {
  flex: 1;
  overflow: hidden;
  display: flex;
  align-items: stretch;
  position: relative;
}
</style>
