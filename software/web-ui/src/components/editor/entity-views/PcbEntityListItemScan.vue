<script setup lang="ts">
import { computed, type PropType } from "vue";
import { BIconEye, BIconEyeFill } from "bootstrap-icons-vue";
import BaseTreeViewItem from "@/components/base/BaseTreeViewItem.vue";
import { usePcbEditorStore } from "@/stores/pcbEditor";
import type { Scan } from "@/models";
const store = usePcbEditorStore();

const props = defineProps({
  scan: {
    type: Object as PropType<Scan>,
    required: true,
  },
});

const scanId = computed(() => {
  return props.scan ? props.scan.name : "UNKNOWN";
});
</script>

<template>
  <base-tree-view-item
    :is-selected="store.isScanSelected(props.scan)"
    @click="store.select({ scans: [props.scan] })"
  >
    <template #header>
      <span>{{ scanId }}</span>
      <span v-if="scan.isTemporary">*</span>
    </template>
    <template #header-buttons>
      <span @click.stop="store.toggleVisibility({ scans: [scan] })">
        <b-icon-eye-fill v-if="scan.isVisible" />
        <b-icon-eye v-else />
      </span>
    </template>
  </base-tree-view-item>
</template>
