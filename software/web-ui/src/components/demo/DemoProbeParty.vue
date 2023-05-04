<script setup lang="ts">
/**
 * PROBOter 'probe party' demo mode control
 */
import { reactive, onMounted, onBeforeUnmount } from "vue";
import { emitter } from "@/globals";
import type { TaskStartedEvent, TaskFinishedEvent } from "@/models";

import BaseForm from "@/components/base/BaseForm.vue";
import BaseButton from "@/components/base/BaseButton.vue";
import BaseFormInput from "@/components/base/BaseFormInput.vue";
import BaseFormGroup from "../base/BaseFormGroup.vue";
import { BIconBalloon } from "bootstrap-icons-vue";

import proboter from "@/api/proboter";

interface State {
  demoModeRunning: boolean;
  feed: number;
  z_offset: number;
}

const state: State = reactive({
  demoModeRunning: false,
  feed: 1000,
  z_offset: -5.0,
});

onMounted(async function () {
  var currentTask = await proboter.taskGetCurrent();

  state.demoModeRunning = currentTask?.name == "ProbeParty";

  emitter.on("TaskStartedEvent", onTaskStartedEvent);
  emitter.on("TaskFinishedEvent", onTaskFinishedEvent);
});

onBeforeUnmount(() => {
  emitter.off("TaskStartedEvent", onTaskStartedEvent);
  emitter.off("TaskFinishedEvent", onTaskFinishedEvent);
});

function onTaskStartedEvent(event: TaskStartedEvent) {
  if (event.name == "ProbeParty") {
    state.demoModeRunning = true;
  }
}

function onTaskFinishedEvent(event: TaskFinishedEvent) {
  if (event.name == "ProbeParty") {
    state.demoModeRunning = false;
  }
}

function toggleDemoMode() {
  if (state.demoModeRunning) {
    proboter.taskCancelCurrent();
  } else {
    proboter.demoProbeParty(state.feed, state.z_offset);
  }
}
</script>

<template>
  <div class="card bg-dark text-white">
    <div class="card-header">
      <div class="row">
        <!-- Entity name / title -->
        <div class="col">
          <div class="clearfix">
            <h5 class="d-inline-block me-1">Probe Party</h5>
            <b-icon-balloon />
          </div>
        </div>
      </div>
    </div>

    <div class="card-body">
      <!-- Main controls-->
      <base-form>
        <!-- Demo mode feed -->
        <base-form-group label="Feed (mm/min)">
          <base-form-input v-model="state.feed" type="number" required />
        </base-form-group>
        <!-- (Safety) Z offset-->
        <base-form-group label="Z offset">
          <base-form-input v-model="state.z_offset" type="number" required />
        </base-form-group>

        <div class="row">
          <div class="col centered">
            <base-button variant="primary" @click="toggleDemoMode">
              {{ state.demoModeRunning ? "Stop" : "Start" }} Demo Mode
            </base-button>
          </div>
        </div>
      </base-form>
    </div>
  </div>
</template>

<style scoped lang="scss">
@import "@/assets/style.scss";

.centered {
  padding: 5px;
  text-align: center;
}
</style>
