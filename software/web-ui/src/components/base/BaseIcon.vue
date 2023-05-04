<script setup lang="ts">
import type { PropType } from "vue";
import { BIconTerminal } from "bootstrap-icons-vue";

const props = defineProps({
  type: {
    type: String as PropType<"uart-terminal">,
    default: "success",
  },
});
</script>

<template>
  <span>
    <b-icon-terminal v-if="props.type == 'uart-terminal'" />
  </span>
</template>
