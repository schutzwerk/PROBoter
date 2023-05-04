<script setup lang="ts">
import { reactive } from "vue";
import BaseForm from "@/components/base/BaseForm.vue";
import BaseFormGroup from "@/components/base/BaseFormGroup.vue";
import BaseButton from "@/components/base/BaseButton.vue";
import BaseInputPinSelection from "@/components/base/BaseInputPinSelection.vue";
import BaseNavigationContainer from "@/components/base/BaseNavigationContainer.vue";
import BaseFormSelect from "@/components/base/BaseFormSelect.vue";
import BaseFormInput from "@/components/base/BaseFormInput.vue";
import BaseProgressOverlay from "@/components/base/BaseProgressOverlay.vue";
import type { SelectOption } from "@/components/base/BaseFormSelect.vue";

import proboter from "@/api/proboter";
import type { Pad } from "@/models";
import log from "js-vue-logger";
import { usePcbEditorStore } from "@/stores/pcbEditor";

const props = defineProps({
  pcbId: {
    type: Number,
    required: true,
  },
});

const pcbEditor = usePcbEditorStore();

type TriggerSource = "ANALOG_INPUT" | "TARGET_POWER";

interface State {
  selectedPins: Array<Pad>;
  triggerSource: TriggerSource;
  triggerLevel: number;
  timeResolution: number;
  duration: number;
  busy: boolean;
  statusText: string;
  analysisResults: Array<object> | null;
  triggerSourceOptions: Array<SelectOption>;
}

const state: State = reactive({
  useRecordedData: true,
  selectedPins: [],
  triggerSource: "ANALOG_INPUT",
  triggerLevel: 3.0,
  timeResolution: 200,
  duration: 5,
  busy: false,
  statusText: "",
  analysisResults: null,
  triggerSourceOptions: [
    { value: "TARGET_POWER", text: "Target power line" },
    { value: "ANALOG_INPUT", text: "Analog input" },
  ],
});

function onStartMeasurement() {
  log.info("[VoltageMeasurementForm] onStartMeasurement");

  // Extract the IDs of the pins
  let pinsToProbe: Array<number> = [];
  state.selectedPins.forEach((pin) => {
    pinsToProbe.push(pin.id);
  });

  log.info(
    "Start voltage signal measurement of " + pinsToProbe.length + " pins"
  );

  state.busy = true;
  state.statusText = "Measuring voltage signals...";

  // Trigger a real voltage signal measurement
  proboter
    .measureVoltageSignals(
      props.pcbId,
      pinsToProbe,
      state.triggerSource,
      state.triggerLevel,
      state.timeResolution,
      state.duration,
      pcbEditor.probingPlaneZ
    )
    .finally(() => {
      state.busy = false;
    });
}
</script>

<template>
  <base-navigation-container
    title="Voltage Measurement"
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
              description="Pins where voltage signals will be measured"
            >
              <base-input-pin-selection
                v-model="state.selectedPins"
                multi-selection
              />
            </base-form-group>

            <!-- Trigger source -->
            <base-form-group
              label="Trigger Source"
              description="Source to trigger the voltage measurement"
            >
              <base-form-select
                v-model="state.triggerSource"
                :options="state.triggerSourceOptions"
              />
            </base-form-group>

            <!-- Trigger level -->
            <base-form-group
              label="Trigger Level"
              description="Voltage level to trigger the measurement"
            >
              <base-form-input v-model="state.triggerLevel" type="number" />
            </base-form-group>

            <!-- Resolution -->
            <base-form-group
              label="Time Resolution"
              description="Voltage measurment time resolution in nanoseconds"
            >
              <base-form-input v-model="state.timeResolution" type="number" />
            </base-form-group>

            <!-- Duration -->
            <base-form-group
              label="Duration"
              description="Voltage measurment duration in seconds"
            >
              <base-form-input v-model="state.duration" type="number" />
            </base-form-group>
          </base-form>
        </div>
      </div>

      <!-- Start button -->
      <div class="row">
        <div class="col">
          <div class="d-flex justify-content-center">
            <base-button
              class="mr-2"
              variant="primary"
              :disabled="state.busy || state.selectedPins.length < 1"
              @click="onStartMeasurement"
              >Measure</base-button
            >
          </div>
        </div>
      </div>

      <!--
    <div v-if="state.analysisResults !== null" class="row mt-4">
      <div class="col">
        <h5>Identified Protocols</h5>
        <div
          class="row"
          v-for="(protocol, protocolIndex) of state.analysisResults"
          :key="protocolIndex"
        >
          <div class="col">
            <b-card body-class="dp-08" header-class="dp-08">
              <template #header>
                <div style="display: flex; flex-flow: row; align-item: bottom">
                  <h3
                    style="display: inline; margin-top: auto; margin-bottom: 0"
                  >
                    {{ protocol.protocolName }}
                  </h3>
                  <h5
                    style="
                      display: inline;
                      margin-top: auto;
                      margin-bottom: 0;
                      margin-left: 0.5em;
                    "
                  >
                    (
                    {{
                      (protocol.identificationRatings[0].rating * 100).toFixed(
                        0
                      )
                    }}
                    %)
                  </h5>
                  <base-button
                    :to="{
                      name: 'uart-terminal',
                      query: {
                        rx: protocol.signals.data1,
                        tx: protocol.signals.data2,
                      },
                    }"
                    variant="secondary"
                    style="margin-left: auto"
                  >
                    <b-icon icon="terminal" />
                  </base-button>
                </div>
              </template>
              <!- Clock Pin ->
              <div class="row" v-if="protocol.protocolName != 'UART'">
                <div class="col">Clock:</div>
                <div class="col">
                  {{
                    protocol.signals.clock ? protocol.signals.clock : "UNKNOWN"
                  }}
                </div>
              </div>

              <!- Data line 1 Pin ->
              <div class="row">
                <div class="col"></div>
                  {{ protocol.protocolName == "UART" ? "RX" : "Data 1" }}:
                </div>
                >
                <div class="col">
                  {{
                    protocol.signals.data1 ? protocol.signals.data1 : "UNKNOWN"
                  }}
                </div>
              </div>

              <!- Data line 2 Pin ->
              <div class="row">
                <div class="col">
                  {{ protocol.protocolName == "UART" ? "TX" : "Data 2" }}:
                </div>
                >
                <div class="col">
                  {{
                    protocol.signals.data2 ? protocol.signals.data2 : "UNKNOWN"
                  }}
                </div>
              </div>
            </b-card>
          </div>
        </div>
      </div>

    </div>
    -->
    </base-progress-overlay>
  </base-navigation-container>
</template>
