<script setup lang="ts">
/*
 * Central dispatcher / handler of UI events in the interactive PCB editor
 */
import { onBeforeUnmount, reactive, ref } from "vue";
import type { OrthographicCamera, Scene, WebGLRenderer } from "three";

import { usePcbEditorStore } from "@/stores/pcbEditor";
import type { ZoomPanControls } from "@/plugins/threejs/threex/controls/useZoomPanControls";
import PcbEventDispatcher from "@/components/editor/events/usePcbEventDispatcher";
import type { PcbEditorStore } from "@/stores/pcbEditor";

const store: PcbEditorStore = usePcbEditorStore();
let eventDispatcher: PcbEventDispatcher;

interface State {
  frame: null;
  hoveredObject: null;
  objectsUnderCursor: [];
  scene: Scene | undefined;
  camera: OrthographicCamera | undefined;
  renderer: WebGLRenderer | undefined;
  zoomPanControls: ZoomPanControls | undefined;
}

const state: State = reactive({
  frame: null,
  hoveredObject: null,
  objectsUnderCursor: [],
  scene: undefined,
  camera: undefined,
  renderer: undefined,
  zoomPanControls: undefined,
});

const overlay = ref<HTMLElement>();

onBeforeUnmount(() => {
  if (state.frame) {
    cancelAnimationFrame(state.frame);
  }
});

function init(
  renderer: WebGLRenderer,
  camera: OrthographicCamera,
  scene: Scene,
  zoomPanControls: ZoomPanControls
) {
  state.renderer = renderer;
  state.camera = camera;
  state.scene = scene;
  state.zoomPanControls = zoomPanControls;

  window.addEventListener("keydown", (event) => onKeyDown(event));

  eventDispatcher = new PcbEventDispatcher(
    state.camera,
    state.scene,
    state.zoomPanControls,
    overlay.value as HTMLDivElement,
    store
  );
}

function onContextMenu(event: MouseEvent) {
  if (eventDispatcher) eventDispatcher.dispatchMouseEvent("contextmenu", event);
  event.preventDefault();
}

function onClick(event: MouseEvent) {
  if (eventDispatcher) eventDispatcher.dispatchMouseEvent("click", event);
}

function onMouseDown(event: MouseEvent) {
  if (eventDispatcher) eventDispatcher.dispatchMouseEvent("mousedown", event);
}

function onMouseWheel(event: MouseEvent) {
  if (eventDispatcher) eventDispatcher.dispatchMouseEvent("mousewheel", event);
}

function onTouchMove(event: TouchEvent) {
  if (eventDispatcher) eventDispatcher.dispatchTouchEvent("touchmove", event);
}

function onTouchStart(event: TouchEvent) {
  if (eventDispatcher) eventDispatcher.dispatchTouchEvent("touchstart", event);
}

function onMouseMove(event: MouseEvent) {
  if (eventDispatcher) eventDispatcher.dispatchMouseEvent("mousemove", event);
}

function onMouseUp(event: MouseEvent) {
  if (eventDispatcher) eventDispatcher.dispatchMouseEvent("mouseup", event);
}

function onKeyDown(event: KeyboardEvent) {
  // Dispatch the key down event to all active handlers
  if (eventDispatcher) eventDispatcher.dispatchKeyboardEvent("keydown", event);
}

defineExpose({ init });
</script>

<template>
  <div
    ref="overlay"
    class="event-overlay"
    tabindex="0"
    @click="onClick"
    @mousewheel="onMouseWheel"
    @mousedown="onMouseDown"
    @mouseup="onMouseUp"
    @mousemove="onMouseMove"
    @contextmenu="onContextMenu"
    @wheel="onMouseWheel"
    @touchmove="onTouchMove"
    @touchstart="onTouchStart"
  ></div>
</template>

<style scoped>
.event-overlay {
  position: absolute;
  width: 100%;
  height: 100%;
  background: transparent;
}
</style>
