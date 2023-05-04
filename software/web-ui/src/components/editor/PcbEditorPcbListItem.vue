<script setup lang="ts">
import type { PropType } from "vue";

import { pcbApi } from "@/api";
import type { Pcb } from "@/models";

import BaseCard from "@/components/base/BaseCard.vue";
import { BIconTrashFill } from "bootstrap-icons-vue";

const props = defineProps({
  pcb: {
    type: Object as PropType<Pcb>,
    required: true,
  },
});

const emit = defineEmits<{
  (e: "delete-pcb", pcb: Pcb): void;
}>();

function fetchPreviewUrl(pcb_id: number) {
  return pcbApi.getPcbPreviewUrl(pcb_id);
}
</script>

<template>
  <base-card class="text-white bg-dark">
    <div class="row p-1">
      <div class="col col-md-2 text-center" style="margin: auto">
        <router-link
          :to="{ name: 'pcb-detail', params: { pcbId: props.pcb.id } }"
        >
          <img :src="fetchPreviewUrl(props.pcb.id)" width="80" />
        </router-link>
      </div>
      <div class="col col-md-8 text-left">
        <router-link
          :to="{ name: 'pcb-detail', params: { pcbId: props.pcb.id } }"
        >
          <div class="row">
            <div class="col">
              <h3>{{ props.pcb.name }}</h3>
            </div>
          </div>
          <div class="row">
            <div class="col">
              <p>
                Scans: {{ props.pcb.numScans }}, Components:
                {{ props.pcb.numComponents }}, Networks:
                {{ props.pcb.numNetworks }}
              </p>
            </div>
          </div>
        </router-link>
      </div>
      <div class="col col-md-2 text-center">
        <div class="btn-wrapper">
          <button
            class="btn btn-danger v-center"
            title="Delete PCB"
            @click="emit('delete-pcb', props.pcb)"
          >
            <BIconTrashFill aria-hidden="true" />
          </button>
        </div>
      </div>
    </div>
  </base-card>
</template>

<style scoped>
a {
  color: white;
  text-decoration: none !important;
}

.btn-wrapper {
  position: relative;
  height: 100%;
}

.v-center {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
}
</style>
