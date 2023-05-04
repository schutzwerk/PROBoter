<script setup lang="ts">
/**
 * Circular option menu item
 *
 */
import { inject, onBeforeUnmount, onMounted, reactive, computed } from "vue";
import log from "js-vue-logger";

export interface MenuItem {
  show(): void;
  hide(): void;
  toggle(): void;
  setGeometry(radius: number, angle: number): void;
}

const props = defineProps({
  toolTip: {
    type: String,
    default: "Tooltip",
  },
  variant: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["click", "upper-close"]);
const registerMenuItem = inject<(item: MenuItem) => void>("registerMenuItem");
const unregisterMenuItem =
  inject<(item: MenuItem) => void>("unregisterMenuItem");

interface State {
  visible: boolean;
  radius: number;
  angle: number;
  menuItem: MenuItem;
}

const state: State = reactive({
  visible: false,
  radius: 100,
  angle: 45,
  menuItem: {
    show,
    hide,
    toggle,
    setGeometry,
  },
});

onMounted(() => {
  if (registerMenuItem) {
    registerMenuItem(state.menuItem);
  }
});

onBeforeUnmount(() => {
  if (unregisterMenuItem) {
    unregisterMenuItem(state.menuItem);
  }
});

function setGeometry(radius: number, angle: number) {
  state.radius = radius;
  state.angle = angle;
}

function show() {
  state.visible = true;
}

function hide() {
  state.visible = false;
}

function toggle() {
  state.visible = !state.visible;
}

function onClick(event: MouseEvent) {
  log.info("onMenutItemClicked");
  emit("upper-close");
  emit("click", event);
}

const outerTransform = computed(
  () => "rotate(" + state.angle + "deg) translate(-" + state.radius + "px)"
);

const innerStyleObject = computed(() => ({
  transform: "rotate(-" + state.angle + "deg)",
  padding: 0,
  margin: 0,
}));
</script>

<template>
  <Transition>
    <li
      v-if="state.visible"
      class="circular-menu-item"
      data-bs-toggle="tooltip"
      :title="props.toolTip"
      @click.prevent="onClick"
    >
      <span :style="innerStyleObject">
        <slot></slot>
      </span>
    </li>
  </Transition>
</template>

<style scoped lang="scss">
.circular-menu-item {
  position: absolute;
  left: -25px;
  top: -25px;
  cursor: pointer;
  width: 50px;
  height: 50px;
  font-size: 1em;
  border-radius: 50%;
  font-size: 1rem;
  background-color: var(--bs-secondary);
  list-style: none;
  margin-bottom: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  transform: v-bind("outerTransform");
}

.v-enter-active,
.v-leave-active {
  transition: all 0.5s ease;
}

.v-enter-from,
.v-leave-to {
  opacity: 0;
  transform: translate(0, 0);
}
</style>
