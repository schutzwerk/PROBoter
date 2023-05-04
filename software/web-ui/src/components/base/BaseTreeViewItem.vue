<script setup lang="ts">
/*
 * A generic tree view item
 */
import { reactive, computed, useSlots } from "vue";

const props = defineProps({
  header: {
    type: String,
    default: "",
  },
  isSelected: {
    type: Boolean,
    default: false,
  },
});

const slots = useSlots();
const emit = defineEmits(["click"]);

const state = reactive({
  isOpen: false,
});

const isGroup = computed(() => {
  return !!slots.default;
});

function toggle(event: MouseEvent) {
  state.isOpen = !state.isOpen;
  const target = event.target as HTMLSpanElement;
  target.classList.toggle("caret-down");
}

function onClick(event: MouseEvent) {
  emit("click", event);
}
</script>

<template>
  <div
    class="tree-view-item"
    :class="{ selected: isSelected }"
    @click.stop="onClick"
  >
    <!-- Header -->
    <div class="header">
      <span v-if="isGroup" class="caret" @click.stop="toggle"></span>
      <span class="header-content">
        <slot name="header">{{ props.header }}</slot>
      </span>
      <span class="header-buttons">
        <slot name="header-buttons"></slot>
      </span>
    </div>

    <!-- List content -->
    <ul v-if="state.isOpen" class="children">
      <slot></slot>
    </ul>
  </div>
</template>

<style scoped>
.tree-view-item {
  text-align: left;
  margin: 2px 0;
}

.tree-view-item .selected {
  border: 1px solid white;
}

.tree-view-item .header {
  cursor: default;
}

.tree-view-item .header:hover {
  font-weight: bold;
}

.header {
  display: flex;
  flex-direction: row;
}

.header .header-buttons {
  margin-left: auto;
  padding-right: 5px;
}

.header .header-content {
  margin-right: 1em;
}

.header-content {
  padding-left: 5px;
}

.children {
  padding-left: 1.5em;
}

.caret {
  cursor: pointer;
  -webkit-user-select: none; /* Safari 3.1+ */
  -moz-user-select: none; /* Firefox 2+ */
  -ms-user-select: none; /* IE 10+ */
  user-select: none;
}

.caret::before {
  content: "\25B6";
  color: white;
  display: inline-block;
  margin-right: 6px;
}

.caret-down::before {
  -ms-transform: rotate(90deg); /* IE 9 */
  -webkit-transform: rotate(90deg); /* Safari */
  transform: rotate(90deg);
}
</style>
