<script setup lang="ts">
/**
 * Component to draw a network on a threejs renderer
 */
import { reactive, computed, ref, type PropType } from "vue";
import MeshThree from "@/plugins/threejs/components/Mesh.vue";
import RingGeometry from "@/plugins/threejs/components/RingGeometry.vue";
import PlaneGeometry from "@/plugins/threejs/components/PlaneGeometry.vue";
import BufferGeometry from "@/plugins/threejs/components/BufferGeometry.vue";
import MeshBasicMaterial from "@/plugins/threejs/components/MeshBasicMaterial.vue";
import LineBasicMaterial from "@/plugins/threejs/components/LineBasicMaterial.vue";
import LineThree from "@/plugins/threejs/components/Line.vue";
import Group from "@/plugins/threejs/components/Group.vue";
import type { Network } from "@/models";

import { usePcbStore } from "@/stores/pcbs";
import { usePcbEditorStore } from "@/stores/pcbEditor";
import { Vector3 } from "three";

const props = defineProps({
  network: {
    type: Object as PropType<Network>,
    required: true,
  },
});

const state = reactive({
  isHovered: false,
});

const store = usePcbStore();
const editor = usePcbEditorStore();
const netMesh = ref();

const networkPins = computed(() => {
  if (!props.network) {
    return [];
  }
  console.log("NETWORK " + props.network.id);
  const pins = store.getNetworkPins(props.network);
  console.log("PINS " + pins);
  return pins;
});

const networkPinCenters = computed(() => {
  if (!networkPins.value) {
    return [];
  }
  let tmpPinCenters = [] as Array<Vector3>;
  networkPins.value.forEach((pin) => {
    tmpPinCenters.push(
      new Vector3(pin.center[0], pin.center[1], pin.center[2])
    );
  });
  return tmpPinCenters;
});

const networkCenter = computed(() => {
  if (networkPins.value.length < 1) {
    return null;
  }

  let networkCenter = new Vector3();

  networkPins.value.forEach((pin) => {
    networkCenter.x += pin.center[0];
    networkCenter.y += pin.center[1];
    networkCenter.z += pin.center[2];
  });

  networkCenter.x /= networkPins.value.length;
  networkCenter.y /= networkPins.value.length;
  networkCenter.z /= networkPins.value.length;

  return networkCenter;
});

const networkCenterArray = computed(() => {
  if (!networkCenter.value) {
    return [];
  }
  return [networkCenter.value.x, networkCenter.value.y, networkCenter.value.z];
});

const userData = computed(() => {
  return {
    type: "NETWORK",
    object: props.network,
    vueObject: netMesh.value,
    isSelectable: true,
  };
});

const color = computed(() => {
  // TODO Distinguish selected and hovered state!
  return editor.isNetworkSelected(props.network) || state.isHovered
    ? 0xffff00
    : 0x111111;
});

function onMouseEnter() {
  state.isHovered = true;
}

function onMouseLeave() {
  state.isHovered = false;
}

function onClick() {
  if (!editor.currentMode) {
    editor.select({
      networks: [props.network],
    });
  }
}

function onTouchStart() {
  if (editor.selection.networks.includes(props.network)) {
    editor.selection.networks = editor.selection.networks.filter(
      (n) => n.id != props.network.id
    );
  } else {
    editor.selection.networks.push(props.network);
  }
}
</script>

<template>
  <group>
    <!-- Visualize the network center as rectangular area -->
    <mesh-three
      v-if="networkCenter"
      ref="netMesh"
      :position="networkCenter"
      :visible="network.isVisible"
      :render-order="editor.renderOrderPcbNetworks"
      :user-data="userData"
      @click.prevent="onClick"
      @mouseenter="onMouseEnter"
      @mouseleave="onMouseLeave"
      @touchstart="onTouchStart"
    >
      <plane-geometry :width="2" :height="2" />
      <mesh-basic-material :color="color" :opacity="0.75" :transparent="true" />
    </mesh-three>

    <!-- Visualize the network with connections from the pins to the network center -->
    <template v-for="pin in networkPins" :key="'lineThree-' + pin.id">
      <line-three
        :visible="network.isVisible"
        :render-order="editor.renderOrderPcbNetworks"
        :user-data="userData"
      >
        <buffer-geometry :vertices="[pin.center, networkCenterArray]" />
        <line-basic-material
          :color="color"
          :opacity="0.75"
          :transparent="true"
        />
      </line-three>
    </template>

    <!-- Create markers arround the pin centers belonging to the network -->
    <template
      v-for="(pinCenter, pinIdx) in networkPinCenters"
      :key="'network-' + network.id + '-pin-' + pinIdx"
    >
      <mesh-three
        :position="pinCenter"
        :visible="network.isVisible"
        :render-order="editor.renderOrderPcbNetworks"
        :user-data="userData"
      >
        <ring-geometry
          :inner-radius="0.6"
          :outer-radius="1.0"
          :theta-segments="24"
        />
        <mesh-basic-material
          :color="color"
          :opacity="0.75"
          :transparent="true"
        />
      </mesh-three>
    </template>
  </group>
</template>
