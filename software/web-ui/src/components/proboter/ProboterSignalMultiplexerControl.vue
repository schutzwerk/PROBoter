<script setup lang="ts">
import { reactive } from "vue";
import { computed } from "@vue/reactivity";

import ProboterEntityContainer from "./ProboterEntityContainer.vue";
import type { EntityStatus } from "@/components/proboter/ProboterEntityContainer.vue";
import ProboterSignalMultiplexerChannel from "@/components/proboter/ProboterSignalMultiplexerChannel.vue";

const props = defineProps({
  multiplexer: {
    type: Object,
    default: null,
  },
});

const state = reactive({
  channels: [1, 2, 3, 4],
});

const multiplexerStatus = computed<EntityStatus>(() => {
  return {
    title: props.multiplexer.connected ? "CONNECTED" : "DISCONNECTED",
    variant: props.multiplexer.connected ? "okay" : "error",
  };
});
</script>

<template>
  <proboter-entity-container
    title="Signal Multiplexer"
    :status="multiplexerStatus"
  >
    <form>
      <div class="row">
        <template
          v-for="(channel, channelIdx) in state.channels"
          :key="'channel_control-' + channel"
        >
          <div class="col-lg-3">
            <ProboterSignalMultiplexerChannel
              :key="'channel_control-' + channelIdx"
              :channel="channel"
              :channel-idx="channelIdx"
            />
          </div>
        </template>
      </div>
    </form>
  </proboter-entity-container>
</template>

<style scoped>
.connection-status-icon {
  display: inline-block;
  vertical-align: middle;
  margin: auto;
  height: 100%;
}
</style>
