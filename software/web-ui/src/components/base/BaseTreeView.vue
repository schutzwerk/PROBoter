<script setup lang="ts">
/*
 * A simple tree view
 */
const props = defineProps({
  header: {
    type: String,
    default: "",
  },
});
</script>

<template>
  <div class="tree-view">
    <!-- TreeView header-->
    <div class="header">
      <slot name="header">{{ props.header }}</slot>
    </div>

    <!-- TreeView items -->
    <ul class="tree-view-items">
      <slot></slot>
    </ul>
  </div>
</template>

<style scoped>
.tree-view {
  display: flex;
  flex-flow: column;
  align-items: stretch;
  justify-content: center;
  max-height: 100%;
}

.header {
  display: flex;
  align-items: stretch;
  font-size: 1.2em;
}

.header .header-content {
  vertical-align: center;
}

.header-buttons {
  margin-left: auto;
}

.tree-view-items {
  margin: 0;
  padding: 0;
  text-align: left;
  max-height: 100%;
  overflow-y: auto;
}
</style>
