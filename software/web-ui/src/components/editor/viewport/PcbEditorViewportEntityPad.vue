<script setup lang="ts">
/**
 * Component to draw a pad on a threejs renderer
 */
import { reactive, computed, ref, type PropType } from "vue";
import ThreeMesh from "@/plugins/threejs/components/Mesh.vue";
import MeshBasicMaterial from "@/plugins/threejs/components/MeshBasicMaterial.vue";
import CircleGeometry from "@/plugins/threejs/components/CircleGeometry.vue";
import { usePcbEditorStore } from "@/stores/pcbEditor";
import { Vector3 } from "three";
import type { Pad } from "@/models";

const props = defineProps({
  pad: {
    type: Object as PropType<Pad>,
    default: null,
  },
});

const state = reactive({
  isHovered: false,
  radius: 0.5,
});

const editor = usePcbEditorStore();
const padMesh = ref();

const padCenter = computed(() => {
  return new Vector3(
    props.pad.center[0],
    props.pad.center[1],
    props.pad.center[2]
  );
});

const userData = computed(() => {
  return {
    type: "PAD",
    object: props.pad,
    vueObject: padMesh.value,
    isSelectable: true,
  };
});

const color = computed(() => {
  // TODO Distinguish selected and hovered state!
  return editor.isPadSelected(props.pad) || state.isHovered
    ? 0xffff00
    : 0xd35400;
});

function onMouseEnter() {
  state.isHovered = true;
}

function onMouseLeave() {
  state.isHovered = false;
}

function onMouseWheel(event: WheelEvent) {
  if (editor.isPadSelected(props.pad)) {
    console.log("onMouseWheel", event);
    state.radius *= event.deltaY > 0 ? 1.1 : 0.9;
    event.preventDefault();
  }
}

function onTouchStart() {
  if (!editor.selection.pads?.includes(props.pad)) {
    editor.selection.pads?.push(props.pad);
  } else {
    editor.selection.pads = editor.selection.pads.filter(
      (p) => p.id != props.pad.id
    );
  }
}

function onClick(event: MouseEvent) {
  if (event.ctrlKey) {
    if (!editor.selection.pads?.includes(props.pad)) {
      editor.selection.pads?.push(props.pad);
    }
  } else {
    editor.select({
      pads: [props.pad],
    });
  }
}
</script>

<template>
  <three-mesh
    ref="padMesh"
    :position="padCenter"
    :visible="props.pad.isVisible"
    :render-order="editor.renderOrderPcbPins"
    :user-data="userData"
    @click.prevent="onClick"
    @mouseenter="onMouseEnter"
    @mouseleave="onMouseLeave"
    @mousewheel="onMouseWheel"
    @touchstart="onTouchStart"
  >
    <circle-geometry :radius="state.radius" :segments="24" />
    <mesh-basic-material :color="color" :opacity="0.9" :transparent="true" />
  </three-mesh>
</template>
