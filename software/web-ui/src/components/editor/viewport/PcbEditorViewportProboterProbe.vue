<script setup lang="ts">
/**
 * Component to render a PROBoter hardware probing unit
 */
import {
  computed,
  onMounted,
  onBeforeUnmount,
  reactive,
  watch,
  type PropType,
} from "vue";
import log from "js-vue-logger";
import { emitter } from "@/globals";
import TWEEN, { type Tween } from "@tweenjs/tween.js";
import Group from "@/plugins/threejs/components/Group.vue";
import PcbEditorViewportProboterAxis from "@/components/editor/viewport/PcbEditorViewportProboterAxis.vue";

import { useProboterStore } from "@/stores/proboter";
import type {
  ProbeType,
  ProbeMoveStartEvent,
  ProbeMoveFinishedEvent,
} from "@/models";
import type { Vector3D } from "@/models";
import { Vector3 } from "three";

const props = defineProps({
  probeType: {
    type: String as PropType<ProbeType>,
    default: "P1",
    validator: (value: string) => {
      return ["P1", "P11", "P2", "P21"].indexOf(value) !== -1;
    },
  },
});

const store = useProboterStore();

interface State {
  position: Vector3D;
  movementTween: Tween<Vector3D> | null;
  movementDestination: Vector3D | null;
}

const state: State = reactive({
  position: [0, 0, 0],
  movementTween: null,
  movementDestination: null,
});

const probe = computed(() => store.getProbeByType(props.probeType));

watch(probe, () => {
  // Update the probe's position only if no animation is currently running
  if (state.movementTween === null) {
    updatePositionFromProbe();
  }
});

onMounted(() => {
  emitter.on("ProbeMoveStartEvent", (event) => {
    onProbeMoveStart(event);
  });
  emitter.on("ProbeMoveFinishedEvent", (event) => {
    onProbeMoveFinished(event);
  });
  updatePositionFromProbe();
});

onBeforeUnmount(() => {
  emitter.off("ProbeMoveStartEvent", onProbeMoveStart);
  emitter.off("ProbeMoveFinishedEvent", onProbeMoveFinished);
});

function onProbeMoveFinished(event: ProbeMoveFinishedEvent) {
  log.info("ProbeMoveFinished event received", event);
  if (event.probeType !== probe.value?.probeType) {
    return;
  }
  if (state.movementTween !== null) {
    state.movementTween.stop();
    Object.assign(state.position, state.movementDestination);
    state.movementDestination = null;
  }
}

function onProbeMoveStart(event: ProbeMoveStartEvent) {
  log.info("ProbeMoveStart event received", event);
  if (event.probeType !== probe.value?.probeType) {
    return;
  }

  // Stop an already running animation
  stopMovementAnimation();

  // Estimate the movement duration in milliseconds
  let pathLength = [
    event.destinationGlobal[0] - event.startGlobal[0],
    event.destinationGlobal[1] - event.startGlobal[1],
    event.destinationGlobal[2] - event.startGlobal[2],
  ];
  let duration_ms =
    (Math.sqrt(
      pathLength[0] * pathLength[0] +
        pathLength[1] * pathLength[1] +
        pathLength[2] * pathLength[2]
    ) /
      (event.feed / 60)) *
    1000;

  // Setup the new movement animation
  state.position = event.startGlobal;
  state.movementDestination = event.destinationGlobal;

  state.movementTween = new TWEEN.Tween(state.position).to(
    state.movementDestination,
    duration_ms
  );
  state.movementTween.onUpdate(function (position) {
    Object.assign(state.position, position);
  });
  state.movementTween.onComplete(function () {
    Object.assign(state.position, state.movementDestination);
    state.movementTween = null;
  });
  state.movementTween.start();
}

function stopMovementAnimation() {
  if (state.movementTween !== null) {
    state.movementTween.stop();
    state.movementTween = null;
  }
}

function updatePositionFromProbe() {
  console.log(probe.value);
  if (probe.value !== null) {
    state.position[0] = probe.value ? probe.value.currentPositionGlobal[0] : 0;
    state.position[1] = probe.value ? probe.value.currentPositionGlobal[1] : 0;
    state.position[2] = probe.value ? probe.value.currentPositionGlobal[2] : 0;
  }
}

const probePositionThree = computed(
  () => new Vector3(state.position[0], state.position[1], state.position[2])
);
</script>

<template>
  <group :position="probePositionThree">
    <pcb-editor-viewport-proboter-axis :probe-type="probeType" :axis="'Z'" />
  </group>
</template>
