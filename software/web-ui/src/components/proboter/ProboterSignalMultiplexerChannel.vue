<script setup lang="ts">
import { reactive } from "vue";
import { computed } from "@vue/reactivity";
import log from "js-vue-logger";

import BaseFormCheckbox from "../base/BaseFormCheckbox.vue";
import { proboter } from "@/api";
import { useProboterStore } from "@/stores/proboter";

const proboterStore = useProboterStore();

const props = defineProps({
  channel: {
    type: Number,
    default: null,
  },
  channelIdx: {
    type: Number,
    default: null,
  },
});

const state = reactive({
  channelLevel: "UNKNOWN",
});

const analogState = computed(
  () =>
    proboterStore.signalMultiplexer?.channelSwitchStates[props.channelIdx] !=
    "D"
);

function onAnalogStateChanged(newState: boolean) {
  if (newState) {
    proboterStore.switchAnalog(props.channel);
  } else {
    proboterStore.switchDigital(props.channel);
  }
}

const pullState = computed(
  () =>
    proboterStore.signalMultiplexer?.channelPullStates[props.channelIdx] ==
    "HIGH"
);

function onPullStateChanged(newState: boolean) {
  if (newState) {
    proboterStore.pullChannel(props.channel);
  } else {
    proboterStore.releaseChannel(props.channel);
  }
}

function test() {
  log.info("Testing channel " + props.channel);
  proboter.testChannel(props.channel).then((res) => {
    state.channelLevel = res.level;
  });
}
</script>

<template>
  <div class="card bg-dark text-white">
    <div class="card-header">
      <h5>{{ "Channel " + channel }}</h5>
    </div>

    <div class="card-body">
      <form>
        <div class="row">
          <div class="col">
            <div class="form-check form-switch">
              <base-form-checkbox
                :id="'digital-button-' + props.channelIdx"
                :model-value="analogState"
                @update:model-value="onAnalogStateChanged"
              />
              <label
                class="form-check-label"
                :for="'digital-button-' + props.channelIdx"
                >Analog</label
              >
            </div>
          </div>
        </div>

        <div class="row">
          <div class="col">
            <div class="form-check form-switch">
              <base-form-checkbox
                name="pull-button"
                role="switch"
                :disabled="analogState"
                :model-value="pullState"
                @update:model-value="onPullStateChanged"
              />
              <label class="form-check-label">Pull</label>
            </div>
          </div>
        </div>

        <div class="row">
          <div class="col">
            <div class="input-group mb-3">
              <input
                class="form-control"
                type="text"
                :value="
                  proboterStore.signalMultiplexer?.channelDigitalLevels[
                    channelIdx
                  ]
                "
                disabled
              />
              <button
                class="btn btn-secondary"
                type="button"
                :disabled="analogState"
                @click="test"
              >
                Test
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>
