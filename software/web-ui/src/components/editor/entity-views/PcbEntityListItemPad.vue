<script setup lang="ts">
import { computed } from "vue";
import type { PropType } from "vue";
import { BIconEye, BIconEyeFill } from "bootstrap-icons-vue";
import BaseTreeViewItem from "@/components/base/BaseTreeViewItem.vue";
import { usePcbEditorStore } from "@/stores/pcbEditor";
import type { Pad } from "@/models";

const props = defineProps({
  pad: {
    type: Object as PropType<Pad>,
    required: true,
  },
});

const editor = usePcbEditorStore();

const padId = computed(() => {
  return props.pad ? props.pad.id : "UNKNOWN";
});
</script>

<template>
  <base-tree-view-item
    :is-selected="editor.isPadSelected(props.pad)"
    @click="editor.select({ pads: [props.pad] })"
  >
    <template #header>
      <span>Pad {{ padId }}</span>
      <span v-if="pad.isTemporary">*</span>
    </template>
    <template #header-buttons>
      <span @click.stop="editor.toggleVisibility({ pads: [props.pad] })">
        <b-icon-eye-fill v-if="pad.isVisible" />
        <b-icon-eye v-else />
      </span>
    </template>
  </base-tree-view-item>
</template>
