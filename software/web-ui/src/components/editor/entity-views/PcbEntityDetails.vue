<script setup lang="ts">
import { computed } from "vue";
import PcbEntityDetailsComponent from "@/components/editor/entity-views/PcbEntityDetailsComponent.vue";
import PcbEntityDetailsPad from "@/components/editor/entity-views/PcbEntityDetailsPad.vue";
import PcbEntityDetailsNetwork from "@/components/editor/entity-views/PcbEntityDetailsNetwork.vue";
import PcbEntityDetailsScan from "@/components/editor/entity-views/PcbEntityDetailsScan.vue";
import { usePcbEditorStore } from "@/stores/pcbEditor";

const store = usePcbEditorStore();

const singleSelectedComponent = computed(() => {
  return store.selection.pads.length < 1 &&
    store.selection.networks.length < 1 &&
    store.selection.scans.length < 1 &&
    store.selection.components.length === 1
    ? store.selection.components[0]
    : null;
});

const singleSelectedPad = computed(() => {
  return store.selection.networks.length < 1 &&
    store.selection.components.length < 1 &&
    store.selection.scans.length < 1 &&
    store.selection.pads.length === 1
    ? store.selection.pads[0]
    : null;
});

const singleSelectedNetwork = computed(() => {
  return store.selection.pads.length < 1 &&
    store.selection.components.length < 1 &&
    store.selection.scans.length < 1 &&
    store.selection.networks.length === 1
    ? store.selection.networks[0]
    : null;
});

const singleSelectedScan = computed(() => {
  return store.selection.pads.length < 1 &&
    store.selection.components.length < 1 &&
    store.selection.networks.length < 1 &&
    store.selection.scans.length == 1
    ? store.selection.scans[0]
    : null;
});
</script>

<template>
  <div v-if="!store.isSelectionEmpty" class="pcb-entity-details-container">
    <pcb-entity-details-component
      v-if="singleSelectedComponent"
      :component="singleSelectedComponent"
    />
    <pcb-entity-details-pad
      v-else-if="singleSelectedPad"
      :pad="singleSelectedPad"
    />
    <pcb-entity-details-network
      v-else-if="singleSelectedNetwork"
      :network="singleSelectedNetwork"
    />
    <pcb-entity-details-scan
      v-else-if="singleSelectedScan"
      :scan="singleSelectedScan"
    />
    <strong v-else>Detail view not implemented yet :(</strong>
  </div>
</template>

<style scoped>
.pcb-entity-details-container {
  text-align: left;
}
</style>
