<script setup lang="ts">
import { computed, type PropType } from "vue";
import BaseForm from "@/components/base/BaseForm.vue";
import BaseFormGroup from "@/components/base/BaseFormGroup.vue";
import PcbEntityDetailContainer from "@/components/editor/entity-views/PcbEntityDetailContainer.vue";
import { usePcbStore } from "@/stores/pcbs";
import type { Network } from "@/models";
import { usePcbEditorStore } from "@/stores/pcbEditor";

const props = defineProps({
  network: {
    type: Object as PropType<Network>,
    default: null,
  },
});

const pcbs = usePcbStore();
const editor = usePcbEditorStore();

const name = computed({
  get() {
    return props.network.name;
  },
  set(value) {
    let newNetwork = JSON.parse(JSON.stringify(props.network));
    newNetwork.name = value;
    pcbs.updateNetwork(newNetwork);
  },
});

function deleteNetwork(network: Network) {
  pcbs.deleteNetwork(network).then(() => {
    editor.selection.networks = editor.selection.networks?.filter(
      (n: Network) => n.id != network.id
    );
  });
}
</script>

<template>
  <pcb-entity-detail-container
    :title="'Network - ' + props.network.name"
    @delete="deleteNetwork(props.network)"
  >
    <base-form>
      <base-form-group label="Name">
        <input v-model="name" type="text" class="form-control" />
      </base-form-group>
    </base-form>
  </pcb-entity-detail-container>
</template>
