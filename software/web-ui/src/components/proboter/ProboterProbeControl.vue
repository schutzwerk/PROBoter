<script setup lang="ts">
import type { PropType } from "vue";
import { reactive, computed } from "vue";
import log from "js-vue-logger";

import type { Probe } from "@/models";

import {
  BIconGear,
  BIconCalculator,
  BIconCheck,
  BIconX,
  BIconArrowsMove,
} from "bootstrap-icons-vue";
import ProboterEntityContainer from "@/components/proboter/ProboterEntityContainer.vue";

import { useProboterStore } from "@/stores/proboter";

const proboter = useProboterStore();

const props = defineProps({
  /**
   * The probe to control
   */
  probe: {
    type: Object as PropType<Probe>,
    default: null,
  },
});

const state = reactive({
  position: {
    x: "0",
    y: "0",
    z: "0",
  },
  isGlobal: false,
  feed: 500,
});

const probeStatusTitle = computed(() =>
  props.probe.moving
    ? "MOVING"
    : props.probe.connected
    ? "CONNECTED"
    : "DISCONNECTED"
);

const probeStatusVariant = computed(() =>
  props.probe.moving ? "warning" : props.probe.connected ? "success" : "danger"
);

const currentPosition = computed<number[]>(() =>
  state.isGlobal
    ? props.probe.currentPositionGlobal
    : props.probe.currentPositionLocal
);

function homeProbe() {
  /**
   * Home the probe
   */
  proboter.homeProbe(props.probe).then(() => {
    log.info("Homing probe " + props.probe.probeType + " in progress");
  });
}

function moveProbe() {
  /**
   * Absolute probe movement
   */
  // Parse the user input
  var position = [
    parseFloat(state.position.x),
    parseFloat(state.position.y),
    parseFloat(state.position.z),
  ];
  // Send the move command
  proboter
    .moveProbe(props.probe, position, state.feed, state.isGlobal)
    .then((response) => {
      log.debug("Moving probe in progress", response);
    });
}

function moveIncremental(axis: "x" | "y" | "z", scale: number) {
  /**
   * Incremental probe movement
   */
  // Parse the user input
  let position = [
    parseFloat(state.position.x),
    parseFloat(state.position.y),
    parseFloat(state.position.z),
  ];
  // Create a copy of the current position
  let newPosition = JSON.parse(JSON.stringify(currentPosition.value));

  // Apply the incremental offsets
  switch (axis) {
    case "x":
      newPosition[0] += scale * position[0];
      break;
    case "y":
      newPosition[1] += scale * position[1];
      break;
    case "z":
      newPosition[2] += scale * position[2];
      break;
  }

  // Finally send the command
  proboter.moveProbe(props.probe, newPosition, state.feed, state.isGlobal);
}
</script>

<template>
  <proboter-entity-container :title="'Probe - ' + probe.probeType">
    <template #status>
      <span
        style="margin-top: auto; margin-bottom: auto"
        :class="['badge', 'rounded-pill', 'bg-' + probeStatusVariant]"
      >
        <div class="d-xxl-inline d-xl-none">{{ probeStatusTitle }}</div>
        <div class="d-xxl-none d-xl-inline">
          <b-icon-check v-if="probeStatusVariant == 'success'" />
          <b-icon-x v-else-if="probeStatusVariant == 'danger'" />
          <b-icon-arrows-move v-else />
        </div>
      </span>
    </template>

    <!-- Controls-->
    <template #controls>
      <router-link
        class="btn btn-secondary me-2"
        title="Settings"
        :to="{
          name: 'probe-settings',
          params: { probeType: props.probe.probeType },
        }"
      >
        <BIconGear aria-hidden="true" />
      </router-link>

      <router-link
        class="btn btn-secondary me-2"
        title="Calibration"
        :to="{
          name: 'probe-calibration',
          params: { probeType: props.probe.probeType },
        }"
      >
        <BIconCalculator aria-hidden="true" />
      </router-link>
    </template>

    <!-- Main probe controls -->
    <form>
      <!-- X-->
      <div class="row">
        <div class="col">
          <div class="input-group">
            <span class="input-group-text" style="width: 8em"
              >X: {{ currentPosition[0].toFixed(3) }}</span
            >
            <input
              v-model="state.position.x"
              type="text"
              class="form-control text-center"
              required
            />
            <button
              class="btn btn-secondary"
              type="button"
              @click="moveIncremental('x', 1)"
            >
              +
            </button>
            <button
              class="btn btn-secondary"
              type="button"
              @click="moveIncremental('x', -1)"
            >
              -
            </button>
          </div>
        </div>
      </div>

      <!-- Y-->
      <div class="row mt-1">
        <div class="col">
          <div class="input-group">
            <span class="input-group-text" style="width: 8em"
              >Y: {{ currentPosition[1].toFixed(3) }}</span
            >
            <input
              v-model="state.position.y"
              type="text"
              class="form-control text-center"
              required
            />
            <button
              class="btn btn-secondary"
              type="button"
              @click="moveIncremental('y', 1)"
            >
              +
            </button>
            <button
              class="btn btn-secondary"
              type="button"
              @click="moveIncremental('y', -1)"
            >
              -
            </button>
          </div>
        </div>
      </div>

      <!-- Z-->
      <div class="row">
        <div class="col">
          <div class="input-group mt-1">
            <span class="input-group-text" style="width: 8em"
              >Z: {{ currentPosition[2].toFixed(3) }}</span
            >
            <input
              v-model="state.position.z"
              type="text"
              class="form-control text-center"
              required
            />
            <button
              class="btn btn-secondary"
              type="button"
              @click="moveIncremental('z', 1)"
            >
              +
            </button>
            <button
              class="btn btn-secondary"
              type="button"
              @click="moveIncremental('z', -1)"
            >
              -
            </button>
          </div>
        </div>
      </div>

      <!--Action buttons-->
      <div class="row mt-2">
        <div class="col">
          <!-- Home button -->
          <button
            type="button"
            class="btn btn-secondary w-100"
            @click="homeProbe()"
          >
            Home
          </button>
        </div>
      </div>

      <!-- Move button -->
      <div class="row mt-2">
        <div class="col">
          <button
            type="button"
            class="btn btn-secondary w-100"
            @click="moveProbe()"
          >
            Move
          </button>
        </div>
      </div>

      <!-- Global / local coordinate switch -->
      <div class="row mt-2">
        <div class="col">
          <div class="form-check">
            <input
              v-model="state.isGlobal"
              type="checkbox"
              class="form-check-input d-inline-block align-middle"
              name="is-global"
              switch
            />
            <label class="form-check-label">Global</label>
          </div>
        </div>
      </div>
    </form>
  </proboter-entity-container>
</template>
