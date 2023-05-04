<script setup lang="ts">
import type { RouteLocation } from "vue-router";
import { onMounted, reactive, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import log from "js-vue-logger";
import { BIconArrowRepeat } from "bootstrap-icons-vue";

import BasePage from "@/components/base/BasePage.vue";
import BaseModal, { type ModalSize } from "@/components/base/BaseModal.vue";
import ProboterProbeControl from "@/components/proboter/ProboterProbeControl.vue";
import ProboterCameraControl from "@/components/proboter/ProboterCameraControl.vue";
import ProboterLightControl from "@/components/proboter/ProboterLightControl.vue";
import ProboterSignalMultiplexerControl from "@/components/proboter/ProboterSignalMultiplexerControl.vue";
import ProboterTargetPowerControl from "@/components/proboter/ProboterTargetPowerControl.vue";

import { useProboterStore } from "@/stores/proboter";

const proboter = useProboterStore();
const router = useRouter();
const route = useRoute();
const routerModal = ref<InstanceType<typeof BaseModal>>();

watch(
  () => route.meta,
  async (newMeta) => {
    if (newMeta.showModal) {
      routerModal.value?.show();
      const getModalTitle = newMeta.modalTitle as (
        route: RouteLocation
      ) => string;
      state.modalTitle = getModalTitle(route);
      state.modalSize = (newMeta.modalSize as ModalSize) || null;
    } else {
      routerModal.value?.hide();
    }
  }
);

interface State {
  reconnecting: boolean;
  modalTitle: undefined | string;
  modalSize: ModalSize;
}
const state: State = reactive({
  reconnecting: false,
  modalTitle: undefined,
  modalSize: null,
});

onMounted(() => {
  if (route.meta.showModal && routerModal.value) {
    routerModal.value?.show();
    const getModalTitle = route.meta.modalTitle as (
      route: RouteLocation
    ) => string;
    state.modalTitle = getModalTitle(route);
    state.modalSize = (route.meta.modalSize as ModalSize) || null;
  }
});

function reconnect() {
  if (state.reconnecting) {
    log.info("Already reconnecting");
    return;
  }

  log.info("Reconnecting PROBoter");
  state.reconnecting = true;
  proboter.reconnectProboter().finally(() => {
    state.reconnecting = false;
  });
}

function onRouterModalHide() {
  router.replace({ name: "proboter-control" });
}
</script>

<template>
  <base-page
    :title="
      'PROBoter - ' +
      (proboter.proboterConfig ? proboter.proboterConfig.name : '')
    "
  >
    <!-- Router Modal-->
    <base-modal
      ref="routerModal"
      :title="state.modalTitle"
      :size="state.modalSize"
      @hide="onRouterModalHide()"
    >
      <router-view
    /></base-modal>

    <!-- Header-->
    <template v-if="proboter.proboterConfig" #header-ext>
      <h4 class="d-inline ms-2">
        <span
          data-bs-toggle="tooltip"
          title="Reconnect"
          @click.prevent="reconnect"
        >
          <b-icon-arrow-repeat
            :class="{ rotate: state.reconnecting }"
            style="cursor: hand"
          />
        </span>
      </h4>
    </template>

    <!-- Camera controls -->
    <div class="row mb-2">
      <!-- Static camera systems -->
      <template
        v-for="camera in proboter.staticCameras"
        :key="'static-camera-control-' + camera.id"
      >
        <div class="col col-xxl-6 col-xl-12">
          <proboter-camera-control :camera="camera" />
        </div>
      </template>
    </div>

    <!-- Probe controls    -->
    <div class="row mt-4">
      <template
        v-for="probe in proboter.probes.sort(
          (p1, p2) => p1.orderIndex - p2.orderIndex
        )"
        :key="'probe-control-' + probe.id"
      >
        <div class="col col-xl-3 col-lg-6 col-md-6 col-sm-12 mb-2">
          <proboter-probe-control :probe="probe" />
        </div>
      </template>
    </div>

    <!-- Signal multiplexer -->
    <div v-if="proboter.signalMultiplexer" class="row mb-2 mt-4">
      <div class="col">
        <ProboterSignalMultiplexerControl
          :multiplexer="proboter.signalMultiplexer"
        />
      </div>
    </div>

    <div class="row mt-4">
      <!-- Light control -->
      <div v-if="proboter.light" class="col col-xl-3 col-lg-12 col-md-12 mb-2">
        <proboter-light-control class="fill-height" />
      </div>

      <!-- Target power control -->
      <div v-if="proboter.power" class="col col-xl-3 col-lg-12 col-md-12 mb-2">
        <proboter-target-power-control class="fill-height" />
      </div>
    </div>
  </base-page>
</template>

<style scoped>
.fill-height {
  height: 100%;
}
</style>
