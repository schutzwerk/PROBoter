<script setup lang="ts">
import { reactive, inject } from "vue";
import { useRouter } from "vue-router";
import proboter from "@/api/proboter";
import log from "js-vue-logger";
import { FAKE_IT_TILL_PROBOTER_MAKES_IT } from "@/globals";

import BaseButton from "@/components/base/BaseButton.vue";
import BaseForm from "@/components/base/BaseForm.vue";
import BaseFormGroup from "@/components/base/BaseFormGroup.vue";
import BaseInputPinSelection from "@/components/base/BaseInputPinSelection.vue";
import BaseFormInput from "@/components/base/BaseFormInput.vue";
import BaseFormCheckGroup from "@/components/base/BaseFormCheckGroup.vue";
import type { CheckGroupOption } from "@/components/base/BaseFormCheckGroup.vue";
import BaseNavigationContainer from "@/components/base/BaseNavigationContainer.vue";
import BaseProgressOverlay from "@/components/base/BaseProgressOverlay.vue";
import type { Pad, ProbeType } from "@/models";
import { usePcbEditorStore } from "@/stores/pcbEditor";
import type { PcbEditorStore } from "@/stores/pcbEditor";
import { usePcbStore } from "@/stores/pcbs";
import type { MessageBox } from "@/App.vue";

const store: PcbEditorStore = usePcbEditorStore();
const pcbStore = usePcbStore();
const router = useRouter();

const messageBox = inject<MessageBox>("messageBox");

interface State {
  selectedProbes: ProbeType[];
  selectedPins: Pad[];
  probeOptions: CheckGroupOption[];
  probingFeed: number;
  busy: boolean;
  statusText: string;
}

const state: State = reactive({
  selectedProbes: ["P11", "P1", "P2", "P21"],
  selectedPins: [],
  probeOptions: [
    { text: "P1.1", value: "P11" },
    { text: "P1", value: "P1" },
    { text: "P2", value: "P2" },
    { text: "P2.1", value: "P21" },
  ],
  probingFeed: 1000,
  busy: false,
  statusText: "",
});

function onStartProbing() {
  // User hint
  messageBox
    ?.confirm("UART adapter disconnected?", "WARNING", "Yes", "No")
    .then((res) => {
      if (!res) {
        log.info("Probing cancelled");
        return;
      }

      log.debug(
        "Start electrical connectivity probing of " +
          state.selectedPins.length +
          " pins"
      );
      state.statusText = "Probing " + state.selectedPins.length + " pins";
      state.busy = true;
      proboter
        .probePinConnectivity(
          store.currentPcbId,
          state.selectedPins,
          state.selectedProbes,
          state.probingFeed,
          store.probingPlaneZ
        )
        .then(() => {
          if (FAKE_IT_TILL_PROBOTER_MAKES_IT) {
            // Create fake network
            log.info("Creating fake network");
            return pcbStore.createNetwork({
              id: -1,
              pcbId: store.currentPcbId,
              name: "Network",
              pinIds: state.selectedPins.map((pin) => pin.id),
              isVisible: true,
              isTemporary: false,
            });
          }
        })
        .then(() => {
          //Note: Figured there is already an API-call, so I decided
          // against writing the algorithm myself
          log.debug("Probing finshed:");
          //initializePcb(this.pcb.id)
          router.replace({ name: "pcb-detail" });
        })
        .finally(() => {
          state.statusText = "";
          state.busy = false;
        });
    });
}
</script>

<template>
  <base-navigation-container
    title="Network Probing"
    :to="{ name: 'pcb-detail' }"
  >
    <base-progress-overlay
      :show="state.busy"
      :text="state.statusText"
      class="dp-08"
    >
      <div class="row">
        <div class="col">
          <base-form>
            <!-- Pin selection -->
            <base-form-group
              label="Pins"
              description="Pins to check for electrical connectivity"
            >
              <base-input-pin-selection
                v-model="state.selectedPins"
                multi-selection
              />
            </base-form-group>

            <!-- Probes to use -->
            <base-form-group
              label="Probes"
              description="Units used for probing"
            >
              <base-form-check-group
                v-model="state.selectedProbes"
                :options="state.probeOptions"
              />
            </base-form-group>

            <!-- Probing feed -->
            <base-form-group
              label="Feed"
              description="Probing feed in mm / min"
            >
              <base-form-input v-model="state.probingFeed" type="text" />
            </base-form-group>
          </base-form>
        </div>
      </div>

      <!-- Start button -->
      <div class="row mt-2">
        <div class="col">
          <div class="d-flex justify-content-center">
            <base-button
              class="mr-2"
              variant="primary"
              :disabled="state.busy || state.selectedPins.length < 2"
              @click="onStartProbing"
              >Probe</base-button
            >
          </div>
        </div>
      </div>
    </base-progress-overlay>
  </base-navigation-container>
</template>
