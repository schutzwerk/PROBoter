<script setup lang="ts">
/**
 * Component to display and control the WebSocket based
 * connection(s) to the main server
 */
import { reactive, onMounted } from "vue";
import log from "js-vue-logger";
import { emitter } from "@/globals";

import { backendConfig } from "@/globals";
import { useProboterStore } from "@/stores/proboter";
import { Events, type EventData } from "@/models";

import { BIconLink, BIconLink45deg } from "bootstrap-icons-vue";

const proboterStore = useProboterStore();

defineProps({
  tiny: {
    type: Boolean,
    default: false,
  },
});

const state = reactive({
  wsConnection: undefined as WebSocket | undefined,
  isConnected: false,
  autoReconnect: false,
  reconnectTimer: undefined as ReturnType<typeof setTimeout> | undefined,
  reconnectInterval: 3000,
  pingTimer: undefined as ReturnType<typeof setTimeout> | undefined,
  pingInterval: 5000,
});

onMounted(() => {
  connect();
  emitter.on(Events.ProbeStatusChangedEvent, (event) => {
    proboterStore.probes = proboterStore.probes.map((probe) =>
      probe.probeType == event.status.probeType ? event.status : probe
    );
  });
  emitter.on(Events.TargetPowerControllerChangedEvent, (event) => {
    proboterStore.power = event.status;
  });
  emitter.on(Events.LightControllerChangedEvent, (event) => {
    proboterStore.light = event.status;
  });
  emitter.on(Events.TaskStartedEvent, (event) => {
    proboterStore.currentTask = {
      id: event.id,
      name: event.name,
      progress: 0,
      status: "RUNNING",
    };
  });
  emitter.on(Events.TaskFinishedEvent, () => {
    proboterStore.currentTask = undefined;
  });
});

function ping() {
  //log.debug("Sending PING");
  state.wsConnection?.send(JSON.stringify({ name: "ping" }));
  state.pingTimer = setTimeout(ping, state.pingInterval);
}

function connect() {
  /*
   * Connect to the global event endpoint
   */
  proboterStore.syncProboterState();

  // Build up the camera feed endpoint URL
  let endpoint_url = backendConfig.proboterEventApi + "/events";
  log.info("Connecting to central events endpoint: " + endpoint_url);

  // Try to connect to the endpoint
  if (state.wsConnection) {
    state.wsConnection.close();
    state.wsConnection = undefined;
  }
  state.wsConnection = new WebSocket(endpoint_url);

  state.wsConnection.onmessage = function (event) {
    // Update the video data
    var parsed_event = JSON.parse(event.data);
    processEvent(parsed_event.name, parsed_event.data);
  };

  state.wsConnection.onopen = function () {
    state.isConnected = true;
    clearTimeout(state.reconnectTimer);
    log.info("Successfully connected to central events endpoint");
    state.pingTimer = setTimeout(ping, state.pingInterval);
    log.info("Started ping timer");
  };

  state.wsConnection.onclose = function () {
    log.info("Connection to central events endpoint closed");
    state.wsConnection = undefined;
    state.isConnected = false;
    if (state.autoReconnect) {
      state.reconnectTimer = setTimeout(connect, state.reconnectInterval);
    }
    if (state.pingTimer) {
      log.info("Clearing ping timer");
      clearTimeout(state.pingTimer);
      state.pingTimer = undefined;
    }
  };

  state.wsConnection.onerror = function (error) {
    log.info("Error occurred in event bus connection:", error);
  };
}

function processEvent(name: string, data: object) {
  if (name.toLowerCase() == "pong") {
    log.debug("Server PONG received");
    return;
  }
  if (name in Events) {
    log.info("Processing event '" + name + "':", data);
    const events = Object.values(Events);
    const event: Events = events[Object.keys(Events).indexOf(name)];
    // TODO Check if type enforcement is okay here!
    emitter.emit(event, data as EventData);
  }
}
</script>

<template>
  <div class="backend-connection-control">
    <span v-if="!tiny" class="me-2">Hardware:</span>

    <div
      v-if="state.isConnected"
      class="badge bg-success rounded-pill"
      :class="{ tiny: tiny }"
    >
      <span v-if="tiny" class="align-middle">
        <BIconLink class="connection-status-icon" />
      </span>
      <span v-else>CONNECTED</span>
    </div>

    <div
      v-else
      class="badge bg-danger rounded-pill align-middle"
      :class="{ tiny: tiny }"
      style="cursor: default"
      @click.stop="connect()"
    >
      <span v-if="tiny" class="tiny">
        <BIconLink45deg class="connection-status-icon" />
      </span>
      <span v-else>DISCONNECTED</span>
    </div>
  </div>
</template>

<style scoped>
.backend-connection-control {
  max-width: 100%;
  overflow-x: hidden;
  text-align: center;
}

.badge.tiny {
  text-align: center;
  padding: 0;
  height: 1.5em;
  width: 1.5em;
  font-size: 1.5em;
  line-height: 1.5em;
  vertical-align: middle;
}

.connection-status-icon {
  display: block;
  margin: auto;
  height: 100%;
}

.badge {
  margin: auto;
}
</style>
