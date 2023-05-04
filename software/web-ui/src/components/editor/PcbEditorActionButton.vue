<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import BaseCircularMenu from "@/components/base/BaseCircularMenu.vue";
import BaseCircularMenuItem from "@/components/base/BaseCircularMenuItem.vue";
import {
  BIconBoundingBoxCircles,
  BIconBezier,
  BIconX,
  BIconPlus,
  BIconCameraFill,
  BIconPinFill,
  BIconLightningFill,
} from "bootstrap-icons-vue";
import BaseIcon from "@/components/base/BaseIcon.vue";
import { usePcbEditorStore } from "@/stores/pcbEditor";
import ComponentCreateEventHandler from "./events/ComponentCreateEventHandler";
import PinCreateEventHandler from "./events/PinCreateEventHandler";
import NetworkCreateEventHandler from "./events/NetworkCreateEventHandler";
import log from "js-vue-logger";

enum Mode {
  NONE = "",
  PIN_CREATE = "PIN_CREATE",
  COMPONENT_CREATE = "COMPONENT_CREATE",
  NETWORK_CREATE = "NETWORK_CREATE",
}

const router = useRouter();
const store = usePcbEditorStore();
const circularButton = ref();

function activateMode(mode: Mode) {
  log.info("[PcbEditorActionButton] ACTIVATE_MODE:", mode);
  if (store.currentMode) {
    store.currentMode.deactivate();
  }

  let newHandler = null;
  switch (mode) {
    case Mode.COMPONENT_CREATE: {
      newHandler = new ComponentCreateEventHandler();
      break;
    }
    case Mode.PIN_CREATE: {
      newHandler = new PinCreateEventHandler();
      break;
    }
    case Mode.NETWORK_CREATE: {
      newHandler = new NetworkCreateEventHandler();
      break;
    }
  }
  if (newHandler) {
    newHandler.activate();
  }
  circularButton.value.close();
}

function onClick() {
  if (store.currentMode) {
    store.currentMode.deactivate();
  } else {
    circularButton.value.toggle();
  }
}

function activateScanCreate() {
  router.push({ name: "scan-new" });
  circularButton.value.toggle();
}

function activateScanAnalysis() {
  router.push({ name: "scan-analysis" });
  circularButton.value.toggle();
}

function activateUartTerminal() {
  router.push({ name: "uart-terminal" });
  circularButton.value.toggle();
}

function activateNetworkReversing() {
  router.push({ name: "network-reversing" });
  circularButton.value.toggle();
}

function activateVoltageMeasurement() {
  router.push({ name: "voltage-measurement" });
  circularButton.value.toggle();
}

const actionButtonStyle = computed(() => ({
  color: "black",
  backgroundColor: store.currentMode
    ? "red"
    : getComputedStyle(document.documentElement).getPropertyValue(
        "--bs-primary"
      ),
}));
</script>

<template>
  <base-circular-menu
    ref="circularButton"
    :radius="80"
    @button-clicked="onClick"
  >
    <template #menu-toggler>
      <div class="action-button" :style="actionButtonStyle">
        <b-icon-plus v-if="!store.currentMode" />
        <b-icon-x v-else />
      </div>
    </template>

    <base-circular-menu-item
      tool-tip="New Pin(s)"
      @click="activateMode(Mode.PIN_CREATE)"
    >
      <b-icon-pin-fill />
    </base-circular-menu-item>

    <base-circular-menu-item
      tool-tip="New Component(s)"
      @click="activateMode(Mode.COMPONENT_CREATE)"
    >
      <b-icon-bounding-box-circles />
    </base-circular-menu-item>

    <base-circular-menu-item
      tool-tip="New Network(s)"
      @click="activateMode(Mode.NETWORK_CREATE)"
    >
      <b-icon-bezier />
    </base-circular-menu-item>

    <base-circular-menu-item
      class="automated-task"
      tool-tip="New Scan"
      @click="activateScanCreate"
    >
      <b-icon-camera-fill />
    </base-circular-menu-item>

    <base-circular-menu-item
      class="automated-task"
      tool-tip="Voltage Measurement"
      @click="activateVoltageMeasurement"
    >
      <b-icon-lightning-fill />
    </base-circular-menu-item>

    <base-circular-menu-item
      class="automated-task"
      tool-tip="UART Terminal"
      @click="activateUartTerminal"
    >
      <base-icon type="uart-terminal" />
    </base-circular-menu-item>

    <base-circular-menu-item
      class="automated-task"
      tool-tip="Network Probing"
      @click="activateNetworkReversing"
    >
      <b-icon-bezier />
    </base-circular-menu-item>

    <base-circular-menu-item
      class="automated-task"
      tool-tip="Scan Analysis"
      @click="activateScanAnalysis"
    >
      <b-icon-pin-fill />
      <b-icon-bounding-box-circles />
    </base-circular-menu-item>
  </base-circular-menu>
</template>

<style scoped>
.action-button {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: var(--bs-primary);
}

.automated-task {
  border: 5px solid var(--bs-primary);
}
</style>
