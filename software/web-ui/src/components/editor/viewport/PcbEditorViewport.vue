<script setup lang="ts">
import { onMounted, reactive, watch, ref } from "vue";
import log from "js-vue-logger";

import Renderer from "@/plugins/threejs/components/Renderer.vue";
import Scene from "@/plugins/threejs/components/Scene.vue";
import OrthographicCamera from "@/plugins/threejs/components/OrthographicCamera.vue";
import AmbientLight from "@/plugins/threejs/components/AmbientLight.vue";
import Group from "@/plugins/threejs/components/Group.vue";
import ZoomPanControls from "@/plugins/threejs/threex/controls/useZoomPanControls";
import * as THREE from "three";

import PcbEditorViewportAxesHelper from "@/components/editor/viewport/PcbEditorViewportAxesHelper.vue";
import PcbEditorEntityProbingArea from "@/components/editor/viewport/PcbEditorViewportProbingArea.vue";
import PcbEditorViewportProboter from "@/components/editor/viewport/PcbEditorViewportProboter.vue";
import PcbEditorViewportEventOverlay from "@/components/editor/viewport/PcbEditorViewportEventOverlay.vue";
import PcbEditorViewportEntityPad from "@/components/editor/viewport/PcbEditorViewportEntityPad.vue";
import PcbEditorViewportEntityComponent from "@/components/editor/viewport/PcbEditorViewportEntityComponent.vue";
import PcbEditorViewportEntityNetwork from "@/components/editor/viewport/PcbEditorViewportEntityNetwork.vue";
import PcbEditorViewportEntityScan from "@/components/editor/viewport/PcbEditorViewportEntityScan.vue";

import { usePcbEditorStore } from "@/stores/pcbEditor";

const props = defineProps({
  cursor: {
    type: String,
    default: "default",
  },
});

const store = usePcbEditorStore();

interface State {
  url: null;
  frame: null;
  camera: null;
  scene: null;
  renderer: null;
  selected_pins: [];
  selected_networks: [];
  selected_components: [];
  zoomPanControls: typeof ZoomPanControls | undefined;
}

const state: State = reactive({
  url: null,
  frame: null,
  camera: null,
  scene: null,
  renderer: null,
  selected_pins: [],
  selected_networks: [],
  selected_components: [],
  zoomPanControls: undefined,
});

// Element references
const renderer = ref<InstanceType<typeof Renderer>>();
const camera = ref<InstanceType<typeof OrthographicCamera>>();
const scene = ref<InstanceType<typeof Scene>>();
const eventOverlay = ref<InstanceType<typeof PcbEditorViewportEventOverlay>>();

watch(
  () => store.viewMode,
  (v) => {
    if (state.zoomPanControls) {
      state.zoomPanControls.enableRotate = v === "3D";
      if (v === "2D") {
        state.zoomPanControls.reset();
      }
    }

    updateAspect();
  }
);

function animate() {
  requestAnimationFrame(animate);
  if (state.zoomPanControls) {
    state.zoomPanControls.update();
  }
  // Dirty fix for lost WebGL context
  // TODO Find reason for context loss (tablet use-case) and fix that!
  if (renderer.value?.threeRenderer.getContext().isContextLost()) {
    log.debug("[PCBEditorViewport] Context lost. Try to restore...");
    renderer.value.threeRenderer.forceContextRestore();
  }
}

function updateAspect() {
  const aspect = window.innerWidth / window.innerHeight;
  const realCamera = camera.value?.threeCamera;
  const frustumSize = camera.value?.frustumSize;
  if (realCamera && frustumSize) {
    realCamera.left = (frustumSize * aspect) / -2;
    realCamera.right = (frustumSize * aspect) / 2;
    realCamera.top = frustumSize / 2;
    realCamera.bottom = -frustumSize / 2;
    realCamera.updateProjectionMatrix();
  }
}

onMounted(() => {
  window.addEventListener("resize", onWindowResize, false);
  function onWindowResize() {
    updateAspect();
  }

  // Setup the zoomPan event handler
  state.zoomPanControls = new ZoomPanControls(
    camera.value?.threeCamera,
    renderer.value?.threeRenderer.domElement
  );
  // Start the animation loop
  animate();

  if (renderer.value && camera.value && scene.value) {
    eventOverlay.value?.init(
      renderer.value?.threeRenderer,
      camera.value?.threeCamera,
      scene.value?.threeScene,
      state.zoomPanControls as typeof ZoomPanControls
    );
  }
});
</script>

<template>
  <div class="pcb-editor">
    <!-- 3D viewport -->
    <renderer ref="renderer" class="viewport">
      <scene ref="scene" :background="store.backgroundColor">
        <!-- Single orthographic camera to render the scene -->
        <orthographic-camera ref="camera" />
        <!-- Ambient light required to visualize the PROBoter 3D geometry-->
        <ambient-light
          :hex="0xefefff"
          :intensity="2"
          :position="new THREE.Vector3(50, 50, 50)"
        />

        <!-- Global coordinate system visual hint -->
        <pcb-editor-viewport-axes-helper
          :rotation="new THREE.Vector3(0, Math.PI, 0)"
        />

        <group :position="new THREE.Vector3(0, 0, -0.1)">
          <!-- Scans-->
          <template
            v-for="scan in store.currentPcb?.scans"
            :key="'scan-' + scan.id"
          >
            <pcb-editor-viewport-entity-scan :scan="scan" />
          </template>
        </group>

        <group>
          <!-- Visual representation of the PROBoter hardware -->
          <pcb-editor-viewport-proboter
            v-if="store.isProboterVisible"
            :rotation="new THREE.Vector3(0, Math.PI, 0)"
          />

          <!-- Overlays -->
          <group
            :position="new THREE.Vector3(0, 0, -0.01)"
            :rotation="new THREE.Vector3(0, Math.PI, 0)"
          >
            <!-- Components -->
            <template
              v-for="comp in store.currentPcb?.components"
              :key="'component-' + comp.id"
            >
              <pcb-editor-viewport-entity-component :component="comp" />
            </template>

            <!-- Pins -->
            <template
              v-for="pad in store.currentPcb?.pads"
              :key="'pad-' + pad.id"
            >
              <pcb-editor-viewport-entity-pad :pad="pad" />
            </template>

            <!-- Networks -->
            <template
              v-for="network in store.currentPcb?.networks"
              :key="'network-' + network.id"
            >
              <pcb-editor-viewport-entity-network :network="network" />
            </template>
          </group>

          <!-- Probing area and visual grid -->
          <pcb-editor-entity-probing-area
            :is-grid-visible="store.isGridVisible"
          />

          <!-- Transparent overlay to capture mouse and keyboard events -->
          <pcb-editor-viewport-event-overlay
            ref="eventOverlay"
            :style="{ cursor: props.cursor }"
          />
        </group>
      </scene>
    </renderer>
  </div>
</template>

<style scoped>
.pcb-editor {
  flex: 1;
  display: flex;
  position: relative;
  height: 100%;
}

.viewport {
  position: absolute;
  width: 100%;
  height: 100%;
}
</style>
