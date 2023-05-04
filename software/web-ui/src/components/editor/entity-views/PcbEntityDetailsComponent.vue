<script setup lang="ts">
import { computed, type PropType } from "vue";
import BaseForm from "@/components/base/BaseForm.vue";
import BaseFormInput from "@/components/base/BaseFormInput.vue";
import BaseFormSelect from "@/components/base/BaseFormSelect.vue";
import BaseFormInputGroup from "@/components/base/BaseFormGroup.vue";
import PcbEntityDetailContainer from "@/components/editor/entity-views/PcbEntityDetailContainer.vue";
import { usePcbStore } from "@/stores/pcbs";
import type { Component } from "@/models";
import { usePcbEditorStore } from "@/stores/pcbEditor";

const props = defineProps({
  component: {
    type: Object as PropType<Component>,
    default: null,
  },
});

const pcbs = usePcbStore();
const editor = usePcbEditorStore();

const componentPackageOptions = [
  { value: "THT", text: "Through Hole (THT)" },
  { value: "SON", text: "Small Outline No Leads (SON)" },
  { value: "SOP", text: "Small Outline (SOP)" },
  { value: "QFN", text: "Quad Flat No Leads (QFN)" },
  { value: "QFT", text: "Quad Flat (QFT)" },
  { value: "UNKNOWN", text: "Unknown" },
];

const name = computed({
  get() {
    return props.component.name;
  },
  set(value: string) {
    let newComponent = JSON.parse(JSON.stringify(props.component));
    newComponent.name = value;
    pcbs.updateComponent(newComponent);
  },
});

const vendor = computed({
  get() {
    return props.component.vendor;
  },
  set(value: string) {
    let newComponent = JSON.parse(JSON.stringify(props.component));
    newComponent.vendor = value;
    pcbs.updateComponent(newComponent);
  },
});

const marking = computed({
  get() {
    return props.component.marking;
  },
  set(newValue: string) {
    let newComponent = JSON.parse(JSON.stringify(props.component));
    newComponent.marking = newValue;
    pcbs.updateComponent(newComponent);
  },
});

const componentPackage = computed({
  get() {
    return props.component.package;
  },
  set(newValue: string) {
    let newComponent = JSON.parse(JSON.stringify(props.component)) as Component;
    newComponent.package = newValue;
    pcbs.updateComponent(newComponent);
  },
});

function deleteComponent(component: Component) {
  pcbs.deleteComponent(component).then(() => {
    editor.selection.components = editor.selection.components?.filter(
      (c: Component) => c.id != component.id
    );
  });
}
</script>

<template>
  <pcb-entity-detail-container
    :title="'Component - ' + props.component.name"
    @delete="deleteComponent(props.component)"
  >
    <base-form>
      <base-form-input-group label="ID">
        <base-form-input type="text" disabled :model-value="component.id" />
      </base-form-input-group>

      <base-form-input-group label="Name">
        <base-form-input v-model="name" type="text" />
      </base-form-input-group>

      <base-form-input-group label="Vendor">
        <base-form-input v-model="vendor" type="text" />
      </base-form-input-group>

      <base-form-input-group label="Marking">
        <textarea v-model="marking" class="form-control" />
      </base-form-input-group>

      <base-form-input-group label="Package">
        <base-form-select
          v-model="componentPackage"
          :options="componentPackageOptions"
        ></base-form-select>
      </base-form-input-group>
    </base-form>
  </pcb-entity-detail-container>
</template>
