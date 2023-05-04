<script setup lang="ts">
import { reactive, onMounted, onBeforeUnmount, ref, nextTick } from "vue";
import { BIconArrowRepeat } from "bootstrap-icons-vue";
import log from "js-vue-logger";

import BaseForm from "@/components/base/BaseForm.vue";
import BaseButton from "@/components/base/BaseButton.vue";
import BaseFormGroup from "@/components/base/BaseFormGroup.vue";
import BaseFormInputGroup from "@/components/base/BaseFormInputGroup.vue";
import BaseInputPinSelection from "@/components/base/BaseInputPinSelection.vue";
import BaseNavigationContainer from "@/components/base/BaseNavigationContainer.vue";
import BaseFormSelect from "@/components/base/BaseFormSelect.vue";
import BaseProgressOverlay from "@/components/base/BaseProgressOverlay.vue";

import proboter from "@/api/proboter";
import type { Pad } from "@/models";

import { usePcbStore } from "@/stores/pcbs";

const props = defineProps({
  pcbId: {
    type: Number,
    default: null,
  },
  rxPinId: {
    type: Number,
    default: null,
  },
  txPinId: {
    type: Number,
    default: null,
  },
  baudrate: {
    type: Number,
    default: null,
  },
});

const pcbStore = usePcbStore();

const state = reactive({
  baudRate: 115200 as number,
  baudRates: [
    { value: 50, text: "50" },
    { value: 110, text: "110" },
    { value: 150, text: "150" },
    { value: 300, text: "300" },
    { value: 1200, text: "1200" },
    { value: 2400, text: "2400" },
    { value: 4800, text: "4800" },
    { value: 9600, text: "9600" },
    { value: 19200, text: "19200" },
    { value: 38400, text: "38400" },
    { value: 57600, text: "57600" },
    { value: 115200, text: "115200" },
    { value: 230400, text: "230400" },
    { value: 460800, text: "460800" },
    { value: 500000, text: "500000" },
  ],
  rxpin: null as Pad | null,
  txpin: null as Pad | null,
  terminalInput: "",
  terminalOutput: "",
  uartSocket: null as WebSocket | null,
  busy: false,
  statusText: "",
});

const terminal = ref<HTMLElement>();

onMounted(() => {
  // Search for the pin ids given as props
  if (props.rxPinId) {
    log.debug("Searching for RX pin with ID:", props.rxPinId);
    //state.rxpin = this.$store.getters['currentPcb/getPinById'](this.rxPinId)
    state.rxpin = pcbStore.getPcbPadById(props.pcbId, props.rxPinId);
  }
  if (props.txPinId) {
    log.debug("Searching for TX pin with ID:", props.txPinId);
    //state.txpin = this.$store.getters['currentPcb/getPinById'](this.txPinId)
    state.txpin = pcbStore.getPcbPadById(props.pcbId, props.txPinId);
  }
  // Check if baudrate was given and is in the list of allowed baudrates
  if (
    props.baudrate &&
    state.baudRates.map((br) => br.value).includes(props.baudrate)
  ) {
    state.baudRate = props.baudrate;
  }

  // Connect to the UART shell endpoint
  log.info("[UartTerminal] Connecting to UART shell endpoint");
  state.uartSocket = proboter.createUartShellSocket();
  state.uartSocket.onopen = onUartConnectionEstablished;
  state.uartSocket.onmessage = onUartData;
  state.uartSocket.onclose = onUartConnectionClosed;
  state.uartSocket.onerror = onUartConnectionError;

  let currentPcb = pcbStore.getPcbById(props.pcbId);

  if (currentPcb === undefined) {
    log.error("No PCB selected!");
    return;
  }
});

onBeforeUnmount(() => {
  state.uartSocket?.close();
});

function onUartData(event: MessageEvent) {
  log.info("UART data received:", event);
  let data = event.data;
  state.terminalOutput += data;
  scrollToTerminalEnd();
}

function onUartConnectionEstablished() {
  log.debug("Connection to backend UART terminal established :)");
}

function onUartConnectionClosed() {
  log.debug("Connection to backend UART terminal closed :(");
}

function onUartConnectionError() {
  log.debug("Connection error :(");
}

function onTerminalInputKeyPress(event: KeyboardEvent) {
  if (event.key === "Enter") {
    sendUartCommand();
  }
}

function sendUartCommand() {
  let command = state.terminalInput + "\n";
  state.terminalOutput += command;
  state.uartSocket?.send(command);
  state.terminalInput = "";
  scrollToTerminalEnd();
}

async function scrollToTerminalEnd() {
  await nextTick();

  if (terminal.value) {
    terminal.value.scrollTop = terminal.value?.scrollHeight;
  }
}

function positionProbes() {
  log.debug("Position probes for UART probing");

  // All pins selected?
  if (!state.rxpin || !state.txpin) {
    log.warn("Not all pins selected");
    state.statusText = "Select all pins";
    return;
  }

  // All pins unique?
  if (state.rxpin == state.txpin) {
    state.statusText = "Pins cannot be the same";
    log.warn("Pins are not unique");
    return;
  }

  // Start positioning
  state.busy = true;
  state.statusText = "Positioning probes...";

  proboter
    .probeUartInterface(state.rxpin, state.txpin, state.baudRate)
    .then(() => {
      log.debug("Sucessfully positioned probes for UART probing");
    })
    .finally(() => {
      state.busy = false;
      state.statusText = "";
    });
}

function clearProbingArea() {
  state.busy = true;
  state.statusText = "Clearing probing area...";
  proboter.clearProbingArea().finally(() => {
    state.busy = false;
    state.statusText = "";
  });
}

function swapPins() {
  let _txpin = state.txpin;
  state.txpin = state.rxpin;
  state.rxpin = _txpin;
}

function deviceReset() {
  state.busy = true;
  state.statusText = "Target reset";
  proboter.resetTarget().finally(() => {
    state.busy = false;
    state.statusText = "";
  });
}
</script>

<template>
  <base-navigation-container
    style="height: 100%"
    title="UART Terminal"
    :to="{ name: 'pcb-detail' }"
  >
    <base-progress-overlay
      class="dp-08"
      :show="state.busy"
      :text="state.statusText"
    >
      <base-form class="uart-terminal-form">
        <!-- Pin selection -->
        <base-form-group label="RX" for="uart-rx-pin" label-cols="2">
          <base-input-pin-selection id="uart-rx-pin" v-model="state.rxpin" />
        </base-form-group>

        <base-form-group label="TX" for="txpin" label-cols="2">
          <base-input-pin-selection id="uart-tx-pin" v-model="state.txpin" />
        </base-form-group>

        <base-button
          title="Swap RX / TX pin"
          style="width: 100%; margin-bottom: 2em"
          @click="swapPins"
        >
          RX
          <b-icon-arrow-repeat />TX
        </base-button>

        <base-form-group label="Baud Rate" label-for="baudrate">
          <base-form-select
            v-model="state.baudRate"
            :options="state.baudRates"
          />
        </base-form-group>

        <!-- Terminal window -->
        <div class="uart-terminal-container mb-2">
          <div class="col" style="height: 100%">
            <p ref="terminal" class="uart-terminal">
              {{ state.terminalOutput }}
            </p>
          </div>
        </div>

        <!-- Terminal input -->
        <div class="row">
          <div class="col">
            <base-form-input-group>
              <input
                id="terminalInput"
                v-model="state.terminalInput"
                type="text"
                class="form-control"
                placeholder="UART command"
                @keypress="onTerminalInputKeyPress"
              />
              <base-button variant="primary" @click="sendUartCommand"
                >Send</base-button
              >
            </base-form-input-group>
            <base-button
              style="width: 100%"
              class="mt-2"
              :disabled="!state.rxpin || !state.txpin"
              @click="positionProbes"
              >Position Probes</base-button
            >

            <base-button
              style="width: 100%"
              class="mt-2"
              @click="clearProbingArea"
              >Clear Probing Area</base-button
            >

            <base-button
              variant="danger"
              style="width: 100%"
              class="mt-2"
              @click="deviceReset"
              >Power Reset</base-button
            >
          </div>
        </div>
      </base-form>
    </base-progress-overlay>
  </base-navigation-container>
</template>

<style scoped lang="scss">
@import "@/assets/style.scss";

.uart-terminal-form {
  display: flex;
  flex-flow: column;
  align-items: stretch;
  height: 100%;
}

.uart-terminal-container {
  height: 100%;
  overflow-y: auto;
}

.uart-terminal {
  height: 100%;
  max-height: 100%;
  padding: 0 10px;
  background: black;
  color: $primary;
  white-space: pre-line;
  font: Inconsolata, monospace;
  font-size: 0.8em;
  overflow: auto;
}
</style>
