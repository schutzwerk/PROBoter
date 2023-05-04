<script setup lang="ts">
import { computed } from "vue";
import { BIconEye, BIconEyeFill } from "bootstrap-icons-vue";
import BaseTreeViewItem from "@/components/base/BaseTreeViewItem.vue";
import { usePcbEditorStore } from "@/stores/pcbEditor";

const props = defineProps({
  network: {
    type: Object,
    default: null,
  },
});

const editor = usePcbEditorStore();

const networkId = computed(() => {
  return props.network ? props.network.id : "UNKNOWN";
});
</script>

<template>
  <base-tree-view-item
    :is-selected="editor.isNetworkSelected(props.network)"
    @click="editor.select({ networks: [props.network] })"
  >
    <template #header>
      <span>Network {{ networkId }}</span>
      <span v-if="network.isTemporary">*</span>
    </template>
    <template #header-buttons>
      <span
        @click.stop="editor.toggleVisibility({ networks: [props.network] })"
      >
        <b-icon-eye-fill v-if="network.isVisible" />
        <b-icon-eye v-else />
      </span>
    </template>
  </base-tree-view-item>
</template>
