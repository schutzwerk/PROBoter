<script setup lang="ts">
/**
 * Circular option menu
 *
 */
import { reactive, provide } from "vue";
import { BIconList, BIconX } from "bootstrap-icons-vue";
import type { MenuItem } from "@/components/base/BaseCircularMenuItem.vue";
import log from "js-vue-logger";

defineExpose({ open, close, toggle });

const props = defineProps({
  radius: {
    type: Number,
    default: 75,
  },
  title: {
    type: String,
    default: null,
  },
});

const emit = defineEmits(["button-clicked"]);

interface State {
  isOpen: boolean;
  menuItems: Array<MenuItem>;
}

const state: State = reactive({
  isOpen: false,
  menuItems: [],
});

function open() {
  state.isOpen = true;
  updateMenu();
}
function close() {
  state.isOpen = false;
  updateMenu();
}

function toggle() {
  log.info("[BaseCircularMenu] toggle");
  state.isOpen = !state.isOpen;
  updateMenu();
}

function updateMenu() {
  let idx = 0;
  for (var child of state.menuItems) {
    console.log("RADIUS:", props.radius);
    child.setGeometry(props.radius, (360 / state.menuItems.length) * idx);
    if (state.isOpen) {
      child.show();
    } else {
      child.hide();
    }
    idx += 1;
  }
}

function onMenuButtonClick() {
  log.info("[BaseCircularMenu] onMenuButtonClick");
  emit("button-clicked");
}

function registerMenuItem(menuItem: MenuItem) {
  log.info("[BaseCircularMenu] registerMenuItem", menuItem);
  state.menuItems.push(menuItem);
  return state.menuItems.length - 1;
}

function unregisterMenuItem(menuItem: MenuItem) {
  log.info("[BaseCircularMenu] unregisterMenuItem", menuItem);
  state.menuItems = state.menuItems.filter((item) => item !== menuItem);
}

provide("registerMenuItem", registerMenuItem);
provide("unregisterMenuItem", unregisterMenuItem);
</script>

<template>
  <div class="circular-menu">
    <div
      class="circular-menu-toggler"
      :title="props.title"
      data-bs-toggle="tooltip"
      @click.prevent="onMenuButtonClick"
    >
      <slot name="menu-toggler">
        <b-icon-x v-if="state.isOpen" />
        <b-icon-list v-else />
      </slot>
    </div>

    <div class="circular-menu-items">
      <slot></slot>
    </div>
  </div>
</template>

<style scoped>
.circular-menu {
  display: flex;
  justify-content: center;
  align-items: center;
}

.circular-menu-toggler {
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
}

.circular-menu-toggler,
.circular-menu-items {
  position: absolute;
}
</style>
