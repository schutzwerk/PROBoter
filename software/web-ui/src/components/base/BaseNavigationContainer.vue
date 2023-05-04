<script setup lang="ts">
/**
 * A base navigation container showing a title for the current route
 */
import { RouterLink } from "vue-router";
import { BIconXCircle } from "bootstrap-icons-vue";

const props = defineProps({
  title: {
    type: String,
    default: "",
  },
  to: {
    type: [String, Object],
    default: null,
  },
});
</script>

<template>
  <div class="base-nav-container">
    <div class="header mb-4">
      <h3 class="d-xxl-inline d-none">
        <router-link :to="props.to" class="me-3">
          <b-icon-x-circle />
        </router-link>
        <span>{{ props.title }}</span>
      </h3>
      <h4 class="d-xxl-none d-inline">
        <router-link :to="props.to" class="me-3">
          <b-icon-x-circle />
        </router-link>
        <span>{{ props.title }}</span>
      </h4>
    </div>

    <div class="content">
      <slot></slot>
    </div>
  </div>
</template>

<style scoped>
.base-nav-container {
  display: flex;
  flex-flow: column;
  align-items: stretch;
  overflow-y: hidden;
}

.header {
  display: flex;
  flex-flow: row;
  text-align: center;
}

.content {
  display: flex;
  flex-flow: column;
  align-items: stretch;
  height: 100%;
  max-height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}

.content {
  height: 100%;
}

.header h4 {
  margin: 0;
  padding: 0;
}
</style>
