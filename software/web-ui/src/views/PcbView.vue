<script setup lang="ts">
import { onMounted, ref, inject, reactive } from "vue";
import { useRouter } from "vue-router";
import log from "js-vue-logger";

import { usePcbStore } from "@/stores/pcbs";
import type { Pcb } from "@/models";

import BasePage from "@/components/base/BasePage.vue";
import BaseProgressOverlay from "@/components/base/BaseProgressOverlay.vue";
import PcbNew from "@/components/editor/forms/NewPcbForm.vue";
import BaseModal from "@/components/base/BaseModal.vue";
import { BIconPlus } from "bootstrap-icons-vue";
import type { MessageBox } from "@/App.vue";
import PcbEditorPcbList from "@/components/editor/PcbEditorPcbList.vue";

const store = usePcbStore();
const router = useRouter();

const messageBox = inject<MessageBox>("messageBox");
const newPcbModal = ref<InstanceType<typeof BaseModal>>();

const state = reactive({
  busy: false,
  isBackendDown: false,
});

onMounted(() => {
  log.debug("Start fetching PCBs");
  state.busy = true;
  store
    .fetchPcbs()
    .then(() => {
      log.debug("Updated PCB list");
      state.isBackendDown = false;
    })
    .catch(() => {
      state.isBackendDown = true;
    })
    .finally(() => {
      state.busy = false;
    });
});

function onCreateNewPcb() {
  log.debug("Creating new PCB instance");
  newPcbModal.value?.show();
}

function onPcbCreated(new_pcb: Pcb) {
  newPcbModal.value?.hide();
  router.push({ name: "scan-new", params: { pcbId: new_pcb.id } });
}

function onStartDeletePcb(pcb: Pcb) {
  messageBox
    ?.confirm(
      "Do you really want to delete PCB '" + pcb.name + "'?",
      "Delete PCB"
    )
    .then((value) => {
      if (value) {
        store.deletePcb(pcb.id);
      }
    });
  log.info("Trigger PCB deletion?");
}
</script>

<template>
  <base-page title="PCBs">
    <base-progress-overlay :show="state.busy" :show-progress="true">
      <!-- New PCB button-->
      <button
        class="btn btn-primary action-button"
        type="button"
        title="Create new PCB"
        :disabled="state.isBackendDown"
        @click="onCreateNewPcb"
      >
        <BIconPlus aria-hidden="true" />
      </button>

      <!-- New PCB modal-->
      <base-modal ref="newPcbModal" title="New PCB">
        <pcb-new @pcb-created="onPcbCreated"></pcb-new>
      </base-modal>

      <!-- PCB list-->
      <pcb-editor-pcb-list
        v-if="!state.isBackendDown"
        @delete-pcb="onStartDeletePcb($event)"
      />
      <div v-else class="row" style="height: 100%">
        <div class="col text-center d-flex">
          <h5 class="d-inline-block" style="margin: auto">
            Storage backend connection failed :/
          </h5>
        </div>
      </div>
    </base-progress-overlay>
  </base-page>
</template>

<style scoped>
.action-button {
  position: absolute;
  bottom: 100px;
  right: 100px;
  width: 70px;
  height: 70px;
  font-size: 2em;
  border-radius: 50%;
  z-index: 100;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
