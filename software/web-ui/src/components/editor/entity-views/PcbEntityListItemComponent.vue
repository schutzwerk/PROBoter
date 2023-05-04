<script setup lang="ts">
import type { PropType } from "vue";
import { BIconEye, BIconEyeFill } from "bootstrap-icons-vue";
import BaseTreeViewItem from "@/components/base/BaseTreeViewItem.vue";
import { usePcbEditorStore } from "@/stores/pcbEditor";
import type { Component } from "@/models";

const props = defineProps({
  component: {
    type: Object as PropType<Component>,
    default: null,
  },
});

const editor = usePcbEditorStore();
</script>

<template>
  <base-tree-view-item
    v-if="props.component"
    :is-selected="editor.isComponentSelected(props.component)"
    @click="editor.select({ components: [props.component] })"
  >
    <template #header>
      <span>{{ component.name }}</span>
      <span v-if="component.isTemporary">*</span>
    </template>

    <template #header-buttons>
      <span
        @click.stop="editor.toggleVisibility({ components: [props.component] })"
      >
        <b-icon-eye-fill v-if="component.isVisible" />
        <b-icon-eye v-else />
      </span>
    </template>
  </base-tree-view-item>
</template>
