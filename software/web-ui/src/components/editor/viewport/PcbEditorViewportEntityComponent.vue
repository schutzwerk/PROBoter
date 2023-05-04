<script setup lang="ts">
/**
 * Component to draw a chip on a threejs renderer
 */
import { reactive, computed, ref, type PropType } from "vue";
import { Shape, Vector2 } from "three";
import ThreeMesh from "@/plugins/threejs/components/Mesh.vue";
import MeshBasicMaterial from "@/plugins/threejs/components/MeshBasicMaterial.vue";
import ShapeGeometry from "@/plugins/threejs/components/ShapeGeometry.vue";
import { usePcbEditorStore } from "@/stores/pcbEditor";
import type { Component } from "@/models";

const props = defineProps({
  component: {
    type: Object as PropType<Component>,
    required: true,
  },
});

const componentMesh = ref();
const editor = usePcbEditorStore();

const state = reactive({
  isHovered: false,
});

const isVisible = computed(() => {
  return props.component ? props.component.isVisible : false;
});

const shape = computed(() => {
  if (props.component === null) {
    return new Shape([]);
  } else {
    let points = [] as Array<Vector2>;
    props.component.contour.forEach((contour) => {
      points.push(new Vector2(contour[0], contour[1]));
    });
    return new Shape(points);
  }
});

const color = computed(() => {
  // TODO Distinguish selected and hovered state!
  return editor.isComponentSelected(props.component) || state.isHovered
    ? 0xffff00
    : 0x85c1e9;
});

const userData = computed(() => {
  return {
    type: "COMPONENT",
    object: props.component,
    vueObject: componentMesh.value,
    isSelectable: true,
  };
});

function onMouseEnter() {
  state.isHovered = true;
}

function onMouseLeave() {
  state.isHovered = false;
}

function onClick() {
  if (!editor.currentMode) {
    editor.select({ components: [props.component] });
  }
}

function onTouchStart() {
  if (editor.selection.components.includes(props.component)) {
    editor.selection.components = editor.selection.components.filter(
      (n) => n.id != props.component.id
    );
  } else {
    editor.selection.components.push(props.component);
  }
}
</script>

<template>
  <three-mesh
    ref="componentMesh"
    :visible="isVisible"
    :render-order="editor.renderOrderPcbComponents"
    :user-data="userData"
    @click.prevent="onClick"
    @mouseenter="onMouseEnter"
    @mouseleave="onMouseLeave"
    @touchstart="onTouchStart"
  >
    <shape-geometry :shapes="shape" />
    <mesh-basic-material :color="color" :opacity="0.3" :transparent="true" />
  </three-mesh>
</template>
