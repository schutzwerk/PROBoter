<script setup lang="ts">
import { usePcbStore } from "@/stores/pcbs";
import PcbEditorPcbListItem from "./PcbEditorPcbListItem.vue";
import type { Pcb } from "@/models";

const emit = defineEmits<{
  (e: "delete-pcb", pcb: Pcb): void;
}>();

const store = usePcbStore();
</script>

<template>
  <div class="row h-100">
    <!-- Individual PCBs -->
    <div v-if="store.pcbs.length > 0" class="col">
      <template v-for="(pcb, pcb_idx) in store.pcbs" :key="'pcb-' + pcb_idx">
        <div class="row">
          <div class="col mb-4 md-12">
            <pcb-editor-pcb-list-item
              :pcb="pcb"
              @delete-pcb="emit('delete-pcb', $event)"
            />
          </div>
        </div>
      </template>
    </div>
    <!-- Empty list-->
    <div v-else class="col text-center d-flex">
      <h5 class="d-inline-block" style="margin: auto">No PCBs defined</h5>
    </div>
  </div>
</template>
