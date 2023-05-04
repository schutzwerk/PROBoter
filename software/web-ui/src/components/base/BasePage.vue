<script setup lang="ts">
const props = defineProps({
  title: { type: String, default: null },
});
</script>

<template>
  <div class="page">
    <!-- Header -->
    <div class="page-header">
      <slot name="header">
        <h1 v-if="title" class="d-xxl-inline d-none text-left">
          {{ props.title }}
          <slot name="header-ext"> </slot>
        </h1>
        <h3 v-if="title" class="d-xxl-none d-inline text-left">
          {{ props.title }}
          <slot name="header-ext"> </slot>
        </h3>
      </slot>
    </div>

    <!-- Content -->
    <div class="page-content">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.page {
  flex: 1;
  display: flex;
  flex-flow: column;
  align-items: stretch;
  max-height: 100%;
}

.page .page-header {
  padding: 1em;
}

.page .page-content {
  flex: 1;
  display: flex;
  flex-flow: column;
  align-items: stretch;
  overflow-x: hidden;
  overflow-y: auto;
  padding-left: 1em;
  padding-right: 1em;
  padding-bottom: 1em;
}
</style>
