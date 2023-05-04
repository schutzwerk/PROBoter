<script setup lang="ts">
import { reactive, computed } from "vue";
import { usePcbEditorStore } from "@/stores/pcbEditor";
import { useProboterStore } from "@/stores/proboter";
import {
  BIconLock,
  BIconUnlock,
  BIconGrid3x3,
  BIconHouse,
  BIconLightbulb,
  BIconLightbulbOff,
  BIconLightning,
  BIconLightningFill,
  BIconXLg,
} from "bootstrap-icons-vue";
import BaseFormInput from "@/components/base/BaseFormInput.vue";
import BaseButton from "@/components/base/BaseButton.vue";
import type { Scan } from "@/models";

interface State {
  probingPlaneZValid: boolean;
  probingPlaneZLocked: boolean;
  selectedScan: Scan | undefined;
}

const state: State = reactive({
  probingPlaneZValid: false,
  probingPlaneZLocked: true,
  selectedScan: undefined,
});

const store = usePcbEditorStore();
const proboter = useProboterStore();

const is2DViewMode = computed(() => store.viewMode === "2D");

function toggleProbingPlaneZLock() {
  state.probingPlaneZLocked = !state.probingPlaneZLocked;
  if (state.probingPlaneZLocked) {
    store.probingPlaneZ = -store.currentPcb.thickness * 0.5;
  }
}

function toggleGridVisibility() {
  store.isGridVisible = !store.isGridVisible;
}

function toggleProboterVisibility() {
  store.isProboterVisible = !store.isProboterVisible;
}

function toggleViewMode() {
  store.viewMode = store.viewMode === "2D" ? "3D" : "2D";
}

function homeProboter() {
  proboter.homeProboter();
}

function toggleTargetPower() {
  proboter.setPower(!proboter.power?.on);
}

function toggleLight() {
  proboter.setLight(!proboter.light?.on);
}

function cancelCurrentTask() {
  if (proboter.currentTask) proboter.cancelCurrentTask();
}
</script>

<template>
  <div
    class="btn-toolbar"
    role="toolbar"
    aria-label="Toolbar with button groups"
  >
    <!-- Probing plane Z -->
    <div class="input-group mx-1" prepend="Z">
      <base-form-input
        v-model="store.probingPlaneZ"
        type="number"
        style="max-width: 70px"
        :disabled="state.probingPlaneZLocked"
      />
      <button
        class="btn btn-secondary"
        :title="
          (state.probingPlaneZLocked ? 'Unlock' : 'Lock') + ' probing plane Z'
        "
        @click="toggleProbingPlaneZLock"
      >
        <b-icon-lock v-if="state.probingPlaneZLocked" />
        <b-icon-unlock v-else />
      </button>
    </div>

    <!-- Toggle UI element visibility -->
    <div class="btn-group mx-1">
      <button
        class="btn btn-secondary"
        type="button"
        title="Grid visibility"
        :pressed="store.isGridVisible"
        @click="toggleGridVisibility"
      >
        <b-icon-grid3x3 />
      </button>

      <button
        class="btn btn-secondary"
        type="button"
        title="View mode"
        @click="toggleViewMode"
      >
        <span v-if="is2DViewMode">2D</span>
        <span v-else>3D</span>
      </button>

      <button
        class="btn btn-secondary"
        type="button"
        title="PROBoter visibility"
        :pressed="store.isProboterVisible"
        @click="toggleProboterVisibility"
      >
        <span>P</span>
      </button>
    </div>

    <!-- PROBOter hardware actions -->
    <div class="btn-group mx-1">
      <button
        class="btn btn-secondary"
        type="button"
        title="Home PROBoter hardware"
        @click="homeProboter"
      >
        <b-icon-house />
      </button>

      <button
        class="btn btn-secondary"
        type="button"
        title="Toggle light"
        @click="toggleLight"
      >
        <b-icon-lightbulb v-if="proboter.light?.on" />
        <b-icon-lightbulb-off v-else />
      </button>

      <button
        class="btn btn-secondary"
        type="button"
        title="Toggle target power"
        :pressed="store.isProboterVisible"
        @click="toggleTargetPower"
      >
        <b-icon-lightning-fill v-if="proboter.power?.on" />
        <b-icon-lightning v-else />
      </button>

      <base-button
        title="Cancel current task"
        :variant="proboter.currentTask ? 'danger' : 'secondary'"
        :pressed="store.isProboterVisible"
        @click="cancelCurrentTask"
      >
        <b-icon-x-lg />
      </base-button>
    </div>
  </div>
</template>
