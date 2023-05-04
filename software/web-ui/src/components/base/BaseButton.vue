<script setup lang="ts">
import type { PropType } from "vue";

const props = defineProps({
  variant: {
    type: String as PropType<"primary" | "secondary" | "danger">,
    default: "secondary",
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  outline: {
    type: Boolean,
    default: false,
  },
});
</script>

<template>
  <button
    :class="['btn', 'btn-' + (props.outline ? 'outline-' : '') + props.variant]"
    type="button"
    data-bs-toggle="tooltip"
    :disabled="props.disabled"
  >
    <slot></slot>
  </button>
</template>
