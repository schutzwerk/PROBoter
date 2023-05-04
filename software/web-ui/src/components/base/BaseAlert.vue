<script setup lang="ts">
import { computed } from "vue";
import type { PropType } from "vue";

const props = defineProps({
  variant: {
    type: String as PropType<
      | "primary"
      | "secondary"
      | "success"
      | "danger"
      | "warning"
      | "info"
      | "light"
      | "dark"
    >,
    default: "success",
  },
});

const alertClasses = computed(() => ["alert", "alert-" + props.variant]);
</script>

<template>
  <div :class="alertClasses" role="alert">
    <slot></slot>
  </div>
</template>
