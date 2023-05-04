<script setup lang="ts">
import {
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
  inject,
  type PropType,
} from "vue";
import {
  Object3D,
  Color,
  BufferGeometry,
  Float32BufferAttribute,
  LineBasicMaterial,
  LineSegments,
  Vector3,
} from "three";
import useObject3D from "./useObject3D";

const props = defineProps({
  name: {
    type: String,
    default: "",
  },
  scale: {
    type: Number,
    default: 1.0,
  },
  position: {
    type: Object as PropType<Vector3>,
    default: () => new Vector3(),
  },
  rotation: {
    type: Object as PropType<Vector3>,
    default: () => new Vector3(),
  },
  renderOrder: {
    type: Number,
    default: 0,
  },
  userData: {
    type: Object,
    default: () => ({}),
  },
  visible: {
    type: Boolean,
    default: true,
  },
  size: {
    type: Object,
    default: () => {
      return [10, 10];
    },
  },
  divisions: {
    type: Object,
    default: () => {
      return [10, 10];
    },
  },
  colorCenterLine: {
    type: Number,
    default: 0x444444,
  },
  colorGrid: {
    type: Number,
    default: 0x888888,
  },
});

watch(
  [
    () => props.size,
    () => props.divisions,
    () => props.colorCenterLine,
    () => props.colorGrid,
  ],
  () => {
    updateGrid();
  }
);

const grid = ref<LineSegments>(new LineSegments());
const parentObj = inject<Object3D>("parentObj");
const { setObj, unsetObj } = useObject3D(props);

onMounted(() => {
  updateGrid();
});

onBeforeUnmount(() => {
  unsetObj();
  (grid.value.material as LineBasicMaterial).dispose();
  grid.value.geometry.dispose();
});

function updateGrid() {
  // Initialization code taken from the original threejs repo:
  // https://github.com/mrdoob/three.js/blob/master/src/helpers/GridHelper.js
  let color1 = new Color(props.colorCenterLine);
  let color2 = new Color(props.colorGrid);

  const center = [props.divisions[0] / 2, props.divisions[1] / 2];
  const step = [
    props.size[0] / props.divisions[0],
    props.size[1] / props.divisions[1],
  ];
  const halfSize = [props.size[0] / 2, props.size[1] / 2];

  const vertices = [];
  const colors = [] as Array<number>;

  // Vertical lines
  let j = 0;
  for (
    let i = 0, k = -halfSize[0];
    i <= props.divisions[0];
    i++, k += step[0]
  ) {
    vertices.push(k, -halfSize[1], 0, k, halfSize[1], 0);

    const color = i === center[0] ? color1 : color2;

    color.toArray(colors, j);
    j += 3;
    color.toArray(colors, j);
    j += 3;
    color.toArray(colors, j);
    j += 3;
    color.toArray(colors, j);
    j += 3;
  }

  // Horizontal lines
  for (
    let i = 0, k = -halfSize[1];
    i <= props.divisions[1];
    i++, k += step[1]
  ) {
    vertices.push(-halfSize[0], k, 0, halfSize[0], k, 0);

    const color = i === center[1] ? color1 : color2;

    color.toArray(colors, j);
    j += 3;
    color.toArray(colors, j);
    j += 3;
    color.toArray(colors, j);
    j += 3;
    color.toArray(colors, j);
    j += 3;
  }

  const geometry = new BufferGeometry();
  geometry.setAttribute("position", new Float32BufferAttribute(vertices, 3));
  geometry.setAttribute("color", new Float32BufferAttribute(colors, 3));

  const material = new LineBasicMaterial({
    vertexColors: true,
    toneMapped: false,
  });

  // Dispose old objects
  unsetObj();
  grid.value.geometry.dispose();
  (grid.value.material as LineBasicMaterial).dispose();

  // Apply newly created object
  grid.value = new LineSegments(geometry, material);
  setObj(grid.value, parentObj);
}
</script>

<template>
  <div></div>
</template>
