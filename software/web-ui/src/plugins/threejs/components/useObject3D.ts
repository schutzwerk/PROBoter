import { defineProps, ref, watch, type ExtractPropTypes } from "vue";
import type { PropType } from "vue";
import { Object3D, Vector3 } from "three";

/*******************************
 * Default properties
 ****** ********************* **/
const object3dProps = defineProps({
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
});

type Object3dProps = Readonly<ExtractPropTypes<typeof object3dProps>>;
export default function (extProps: Object3dProps) {
  const props = extProps;

  // The current ThreeJS object initially created here
  const curObj = ref<Object3D | undefined>(undefined);
  const parentObj = ref<Object3D | undefined>(undefined);

  // Internal watchers
  watch(
    () => props.name,
    (newName) => {
      if (curObj.value && newName !== undefined) {
        curObj.value.name = newName;
      }
    }
  );
  watch(
    () => props.scale,
    (newScale) => {
      if (!curObj.value || newScale === undefined) return;
      if (newScale && typeof newScale === "number") {
        curObj.value.scale.x = newScale;
        curObj.value.scale.y = newScale;
        curObj.value.scale.z = newScale;
      }
      Object.assign(curObj.value.scale, newScale);
    }
  );
  watch(
    () => props.position,
    (newPosition) => {
      if (curObj.value && newPosition !== undefined)
        Object.assign(curObj.value.position, newPosition);
    },
    { deep: true }
  );
  watch(
    () => props.rotation,
    (newRotation) => {
      if (curObj.value && newRotation !== undefined)
        Object.assign(curObj.value.rotation, newRotation);
    },
    { deep: true }
  );
  watch(
    () => props.userData,
    (newUserData) => {
      if (curObj.value) Object.assign(curObj.value.userData, newUserData);
    },
    { deep: true }
  );
  watch(
    () => props.visible,
    (newVisible) => {
      if (curObj.value && newVisible !== undefined)
        curObj.value.visible = newVisible;
    }
  );
  watch(
    () => props.renderOrder,
    (newRenderOrder) => {
      if (curObj.value && newRenderOrder !== undefined)
        curObj.value.renderOrder = newRenderOrder;
    }
  );

  function setObj(obj: Object3D, parent: Object3D | undefined = undefined) {
    curObj.value = obj;

    if (obj) {
      obj.name = props.name || obj.name || obj.type;
      // Sync. the object properties
      Object.assign(obj.scale, props.scale);
      Object.assign(obj.position, props.position);
      Object.assign(obj.rotation, props.rotation);
      obj.renderOrder = props.renderOrder || 0;
      obj.visible = props.visible || true;
      Object.assign(obj.userData, props.userData);
    }

    parentObj.value = parent;
    if (parentObj.value && obj) {
      parentObj.value.add(obj);
    }
  }

  function unsetObj() {
    if (parentObj.value && curObj.value) {
      parentObj.value.remove(curObj.value);
    }
  }

  function dispatchEvent(
    el: HTMLElement,
    name: string,
    detail: object,
    options = {}
  ) {
    // https://developer.mozilla.org/en-US/docs/Web/Guide/Events/Creating_and_triggering_events
    const e = new CustomEvent(name, {
      detail,
      bubbles: true,
      cancelable: true,
      ...options,
    });
    return el.dispatchEvent(e);
  }

  return {
    setObj,
    unsetObj,
    dispatchEvent,
  };
}
