<script setup lang="ts">
/**
 * Component to render a PROBoter hardware probe axis
 */
import {
  onMounted,
  watch,
  inject,
  onBeforeUnmount,
  toRaw,
  reactive,
  type PropType,
} from "vue";
import log from "js-vue-logger";
import * as THREE from "three";
import { OBJLoader } from "three/examples/jsm/loaders/OBJLoader";
import { MTLLoader } from "three/examples/jsm/loaders/MTLLoader";
import useObject3D from "@/plugins/threejs/components/useObject3D";

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
    type: Object as PropType<THREE.Vector3>,
    default: () => new THREE.Vector3(),
  },
  rotation: {
    type: Object as PropType<THREE.Vector3>,
    default: () => new THREE.Vector3(),
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
  probeType: {
    type: String,
    default: "P1",
    validator: function (value: string) {
      return ["P1", "P11", "P2", "P21"].indexOf(value) !== -1;
    },
  },
  axis: {
    type: String,
    default: "Z",
    validator: function (value: string) {
      return ["X", "Y", "Z"].indexOf(value) !== -1;
    },
  },
  detailed: {
    type: Boolean,
    default: false,
  },
  edgeColor: {
    type: Number,
    default: 0x101010,
  },
  edgeMinAngle: {
    type: Number,
    default: 30,
  },
});

watch([() => props.probeType, () => props.axis], () => {
  updateModel();
});

const curObj = new THREE.Group();
const parentObj = inject<THREE.Object3D>("parentObj");
const { setObj, unsetObj } = useObject3D(props);

interface State {
  model: THREE.Mesh | undefined;
  edges: THREE.LineSegments | undefined;
}

const state = reactive<State>({
  model: undefined,
  edges: undefined,
});

onMounted(() => {
  log.info("[PcbEditorViewportProboterAxis] onMounted");
  // 180° rotation around the Y-axis is required from the
  // original CAD model orientation
  updateModel();
  setObj(curObj, toRaw(parentObj));
  curObj.rotation.y = Math.PI;
  curObj.rotation.z = Math.PI;
});

onBeforeUnmount(() => {
  log.info("[PcbEditorViewportProboterAxis] onBeforeUnmount");
  unsetObj();

  // ThreeJS object cleanup
  log.debug("[PcbEditorViewportProboterAxis] Disposing edge contours");
  state.edges?.geometry.dispose();
  (state.edges?.material as THREE.LineBasicMaterial).dispose();

  log.debug("[PcbEditorViewportProboterAxis] Disposing model");
  state.model?.geometry.dispose();
  (state.model?.material as Array<THREE.Material>).forEach((mat) => {
    mat.dispose();
  });
});

function updateModel() {
  // 0. Determine the resoure URLs
  let baseUrl =
    "/models/" +
    (props.detailed ? "detailed/" : "") +
    props.axis.toLowerCase() +
    props.probeType.substring(1);
  let materialUrl = baseUrl + ".mtl";
  let modelUrl = baseUrl + ".obj";

  // 1. Load the referenced MTL color / material library
  const materialLoader = new MTLLoader();
  materialLoader.load(materialUrl, (materials) => {
    materials.preload();
    log.info("[PcbEditorViewportProboterAxis] Materials loaded");

    // 2. Load the actual model geometry
    let loader = new OBJLoader();
    loader.setMaterials(materials);
    loader.load(
      modelUrl,
      (obj) => {
        // The actual Mesh object is the first child of the loaded OBJ objects
        let modelMesh = obj.children[0] as THREE.Mesh;

        // Create a new EdgesGeometry to either allow a wire frame visual
        // representation or to make the geometry look more crisp ;)
        let edges = new THREE.EdgesGeometry(
          modelMesh.geometry,
          props.edgeMinAngle
        );
        let modelEdges = new THREE.LineSegments(
          edges,
          new THREE.LineBasicMaterial({ color: props.edgeColor })
        );

        // Remove any existing old model
        curObj.clear();

        // Add the geometry mesh and edges
        curObj.add(modelMesh);
        curObj.add(modelEdges);

        // Store references for later cleanup
        state.model = modelMesh as THREE.Mesh;
        state.edges = modelEdges;

        log.info(
          "[PcbEditorViewportProboterAxis] " +
            "Successfully loaded model of probe axis " +
            props.probeType +
            "-" +
            props.axis
        );
      },
      undefined,
      (error) => {
        log.error("On error:", error);
      }
    );
  });
}
</script>

<template>
  <div></div>
</template>
