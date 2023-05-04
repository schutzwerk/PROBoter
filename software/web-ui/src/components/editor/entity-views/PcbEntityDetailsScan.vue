<script setup lang="ts">
import type { PropType } from "vue";
import BaseForm from "@/components/base/BaseForm.vue";
import BaseFormInputGroup from "@/components/base/BaseFormGroup.vue";
import PcbEntityDetailContainer from "@/components/editor/entity-views/PcbEntityDetailContainer.vue";
import { usePcbStore } from "@/stores/pcbs";
import type { Scan } from "@/models";
import { pcbApi } from "@/api";
import { usePcbEditorStore } from "@/stores/pcbEditor";

const props = defineProps({
  scan: {
    type: Object as PropType<Scan>,
    required: true,
  },
});

const pcbs = usePcbStore();
const editor = usePcbEditorStore();

function deleteScan() {
  pcbs.deleteScan(props.scan).then((deleted) => {
    editor.selection.scans = editor.selection.scans?.filter(
      (s) => s.id != deleted.id
    );
  });
}
</script>

<template>
  <pcb-entity-detail-container
    :title="'Scan - ' + props.scan.name"
    @delete="deleteScan()"
  >
    <div class="row mt-2">
      <div class="col">
        <div class="d-flex justify-content-center">
          <img :src="pcbApi.getScanPreviewUrl(props.scan)" />
        </div>
      </div>
    </div>

    <base-form>
      <base-form-input-group label="ID">
        <input
          type="text"
          disabled
          :value="props.scan.id"
          class="form-control"
        />
      </base-form-input-group>

      <base-form-input-group label="Name">
        <input
          type="text"
          disabled
          :value="props.scan.name"
          class="form-control"
        />
      </base-form-input-group>
    </base-form>
  </pcb-entity-detail-container>
</template>
