import { defineProps, ref, watch, type ExtractPropTypes } from "vue";
import {
  type Line,
  Material,
  Mesh,
  DoubleSide,
  MeshBasicMaterial,
  FrontSide,
} from "three";

/*******************************
 * Default properties
 ****** ********************* **/
const materialProps = defineProps({
  name: {
    type: String,
    default: undefined,
  },
  opacity: {
    type: Number,
    default: 1.0,
  },
  side: {
    type: Number,
    default: DoubleSide,
  },
  transparent: {
    type: Boolean,
    default: false,
  },
  userData: {
    type: Object,
    default: null,
  },
  visible: {
    type: Boolean,
    default: true,
  },
});

type MaterialProps = Readonly<ExtractPropTypes<typeof materialProps>>;
export default function (extProps: MaterialProps) {
  const props = extProps;

  watch(
    () => props.name,
    (newName) => {
      if (curObj.value && newName !== undefined) {
        curObj.value.name = newName;
      }
    }
  );
  watch(
    () => props.opacity,
    (newOpacity) => {
      if (curObj.value && newOpacity !== undefined) {
        curObj.value.opacity = newOpacity;
      }
    }
  );
  watch(
    () => props.side,
    (newSide) => {
      if (curObj.value && newSide !== undefined) {
        curObj.value.side = newSide;
      }
    }
  );
  watch(
    () => props.transparent,
    (newTransparent) => {
      if (curObj.value && newTransparent !== undefined) {
        curObj.value.transparent = newTransparent;
      }
    }
  );
  watch(
    () => props.userData,
    (newUserData) => {
      if (curObj.value) {
        curObj.value.userData = newUserData;
      }
    }
  );
  watch(
    () => props.visible,
    (newVisible) => {
      if (curObj.value && newVisible !== undefined) {
        curObj.value.visible = newVisible;
      }
    }
  );

  // The current ThreeJS material injected by derived components
  const curObj = ref<Material | undefined>(undefined);
  const curMesh = ref<Mesh | Line | undefined>(undefined);

  function setObj(obj: Material, mesh: Mesh | Line | undefined = undefined) {
    curObj.value = obj;
    curMesh.value = mesh;

    // Sync. the object properties
    if (obj) {
      obj.name = props.name || obj.name || obj.type;
      obj.side = props.side || FrontSide;
      obj.userData = props.userData;
      obj.visible = props.visible || true;
      obj.opacity = props.opacity || 1.0;
      obj.transparent = props.transparent || false;
    }

    if (curMesh.value) {
      curMesh.value.material = obj;
    }
  }

  function unsetObj() {
    if (curMesh.value) {
      curMesh.value.material = new MeshBasicMaterial();
    }
  }

  return { setObj, unsetObj };
}
