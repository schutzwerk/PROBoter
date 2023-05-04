<script setup lang="ts">
import { computed } from "vue";
import { BIconEye, BIconEyeFill } from "bootstrap-icons-vue";
import BaseTreeView from "@/components/base/BaseTreeView.vue";
import BaseTreeViewItem from "@/components/base/BaseTreeViewItem.vue";
import PcbEntityListItemPin from "@/components/editor/entity-views/PcbEntityListItemPad.vue";
import PcbEntityListItemNetwork from "@/components/editor/entity-views/PcbEntityListItemNetwork.vue";
import PcbEntityListItemScan from "@/components/editor/entity-views/PcbEntityListItemScan.vue";
import PcbEntityListItemComponent from "@/components/editor/entity-views/PcbEntityListItemComponent.vue";
import type { VisualEntity } from "@/models";

import { usePcbEditorStore } from "@/stores/pcbEditor";

const store = usePcbEditorStore();

const hasNoEntities = computed(() => {
  return (
    store.currentPcb?.components.length === 0 &&
    store.currentPcb?.networks.length === 0 &&
    store.currentPcb?.pads.length === 0
  );
});

const allComponentVisibility = computed(() => {
  return calcAllEntityVisibility(store.currentPcb.components);
});

const allNetworkVisibility = computed(() => {
  return calcAllEntityVisibility(store.currentPcb.networks);
});

const allPadVisibility = computed(() => {
  return calcAllEntityVisibility(store.currentPcb.pads);
});

function calcAllEntityVisibility(entities: Array<VisualEntity>) {
  let visibleEntities = false;
  let invisibleEntities = false;
  entities.forEach((e) => {
    visibleEntities = visibleEntities || e.isVisible;
    invisibleEntities = invisibleEntities || !e.isVisible;
  });
  if (visibleEntities && !invisibleEntities) {
    return "VISIBLE";
  } else if (!visibleEntities && invisibleEntities) {
    return "INVISIBLE";
  } else {
    return "MIXED";
  }
}

function toggleComponentsVisiblitiy() {
  store.setVisibility(
    {
      components: store.currentPcb?.components,
      pads: [],
      networks: [],
      scans: [],
    },
    allComponentVisibility.value === "INVISIBLE"
  );
}

function toggleNetworksVisiblitiy() {
  store.setVisibility(
    {
      components: [],
      pads: [],
      networks: store.currentPcb?.networks,
      scans: [],
    },
    allNetworkVisibility.value === "INVISIBLE"
  );
}

function togglePinsVisiblitiy() {
  store.setVisibility(
    {
      components: [],
      pads: store.currentPcb?.pads,
      networks: [],
      scans: [],
    },
    allPadVisibility.value === "INVISIBLE"
  );
}
</script>

<template>
  <!-- TreeView of visible / selected components -->
  <div class="pcb-entity-list" @click="store.clearSelection()">
    <div v-if="hasNoEntities || !store.currentPcb" class="empty-placeholder">
      <span>No entities defined</span>
    </div>

    <base-tree-view v-else class="entity-tree" @click="store.clearSelection()">
      <!-- Components -->
      <base-tree-view-item v-if="store.currentPcb.components.length > 0">
        <template #header
          >Components ({{ store.currentPcb.components.length }})</template
        >
        <template #header-buttons>
          <b-icon-eye-fill
            v-if="allComponentVisibility !== 'INVISIBLE'"
            :class="{ tristate: allComponentVisibility === 'MIXED' }"
            @click.stop="toggleComponentsVisiblitiy"
          />
          <b-icon-eye v-else @click.stop="toggleComponentsVisiblitiy" />
        </template>
        <pcb-entity-list-item-component
          v-for="comp in store.currentPcb.components"
          :key="'component-' + comp.id"
          :component="comp"
        />
      </base-tree-view-item>

      <!-- Networks -->
      <base-tree-view-item v-if="store.currentPcb.networks.length > 0">
        <template #header
          >Networks ({{ store.currentPcb.networks.length }})</template
        >
        <template #header-buttons>
          <b-icon-eye-fill
            v-if="allNetworkVisibility !== 'INVISIBLE'"
            :class="{ tristate: allNetworkVisibility === 'MIXED' }"
            @click.stop="toggleNetworksVisiblitiy"
          />
          <b-icon-eye v-else @click.stop="toggleNetworksVisiblitiy" />
        </template>
        <pcb-entity-list-item-network
          v-for="network in store.currentPcb.networks"
          :key="'network-' + network.id"
          :network="network"
        />
      </base-tree-view-item>

      <!-- Pads -->
      <base-tree-view-item v-if="store.currentPcb.pads.length > 0">
        <template #header>Pads ({{ store.currentPcb.pads.length }})</template>
        <template #header-buttons>
          <b-icon-eye-fill
            v-if="allPadVisibility !== 'INVISIBLE'"
            :class="{ tristate: allPadVisibility === 'MIXED' }"
            @click.stop="togglePinsVisiblitiy"
          />
          <b-icon-eye v-else @click.stop="togglePinsVisiblitiy" />
        </template>
        <pcb-entity-list-item-pin
          v-for="pad in store.currentPcb.pads"
          :key="'pad-' + pad.id"
          :pad="pad"
        />
      </base-tree-view-item>

      <!-- Scans -->
      <base-tree-view-item v-if="store.currentPcb.scans.length > 0">
        <template #header>Scans ({{ store.currentPcb.scans.length }})</template>
        <pcb-entity-list-item-scan
          v-for="scan in store.currentPcb.scans"
          :key="'scan-' + scan.id"
          :scan="scan"
        />
      </base-tree-view-item>
    </base-tree-view>

    <!-- Optional footer -->
    <div>
      <slot name="footer"></slot>
    </div>
  </div>
</template>

<style scoped>
.pcb-entity-list {
  justify-content: center;
  min-width: 300px;
  max-height: 100%;
}

.tristate {
  color: gray;
}

.empty-placeholder {
  width: 100%;
  height: 100%;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
