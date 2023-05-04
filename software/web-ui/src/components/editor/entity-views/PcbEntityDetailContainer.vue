<script setup lang="ts">
import { BIconTrashFill } from "bootstrap-icons-vue";
import BaseButton from "@/components/base/BaseButton.vue";

const props = defineProps({
  title: { type: String, default: null },
});
const emit = defineEmits(["delete"]);
</script>

<template>
  <div class="entity-container">
    <!-- Header -->
    <div class="entity-container-header">
      <slot name="header">
        <div class="d-flex">
          <h3
            v-if="title"
            class="d-xxl-inline d-xl-none text-left"
            style="margin-right: auto"
          >
            {{ props.title }}
          </h3>
          <h4
            v-if="title"
            class="d-xxl-none d-xl-inline text-left"
            style="margin-right: auto"
          >
            {{ props.title }}
          </h4>
          <base-button variant="danger" @click="emit('delete')">
            <BIconTrashFill aria-hidden="true" />
          </base-button>
        </div>
      </slot>
    </div>

    <!-- Content -->
    <div class="entity-container-content">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.entity-container {
  flex: 1;
  display: flex;
  flex-flow: column;
  align-items: stretch;
  max-height: 100%;
}

.entity-container .entity-container-header {
  margin-bottom: 1em;
}

.entity-container .entity-container-content {
  flex: 1;
  display: flex;
  flex-flow: column;
  align-items: stretch;
  overflow-x: hidden;
  overflow-y: auto;
}
</style>
