<script setup lang="ts">
import { computed, type PropType } from "vue";
import BaseForm from "@/components/base/BaseForm.vue";
import BaseFormGroup from "@/components/base/BaseFormGroup.vue";
import PcbEntityDetailContainer from "@/components/editor/entity-views/PcbEntityDetailContainer.vue";
import { usePcbEditorStore } from "@/stores/pcbEditor";
import { usePcbStore } from "@/stores/pcbs";
import type { Network, Pad, Component } from "@/models";

const props = defineProps({
  pad: {
    type: Object as PropType<Pad>,
    default: null,
  },
});

const pcbs = usePcbStore();
const editor = usePcbEditorStore();

const name = computed({
  get() {
    if (props.pad.name == null) {
      return "Pin " + props.pad.id;
    }
    return props.pad.name;
  },
  set(value) {
    let newPad = JSON.parse(JSON.stringify(props.pad));
    newPad.name = value;
    pcbs.updatePad(newPad);
  },
});

const network = computed({
  get() {
    var _network = editor.currentPcb.networks.filter((obj) => {
      return obj.id === props.pad.networkId;
    });
    return _network[0];
  },
  set(value: Network) {
    let newPad = JSON.parse(JSON.stringify(props.pad)) as Pad;
    newPad = setNameIfNull(newPad);
    newPad.networkId = value.id;
    pcbs.updatePad(newPad);
  },
});

const component = computed({
  get() {
    var _component = editor.currentPcb.components.filter((obj) => {
      return obj.id === props.pad.componentId;
    });
    return _component[0];
  },
  set(value: Component) {
    let newPad = JSON.parse(JSON.stringify(props.pad));
    if (value == null) {
      newPad.componentId = null;
      console.log(
        "Update of pin component to None (null) currently not supported:"
      );
    } else {
      newPad.componentId = value.id;
    }
    pcbs.updatePad(newPad);
  },
});

// Dirty workaround to avoid errors if name is null
function setNameIfNull(pin: Pad) {
  if (pin.name == null) {
    pin.name = "Pin " + pin.id;
  }
  return pin;
}

function deletePad(pad: Pad) {
  pcbs.deletePad(pad).then(() => {
    editor.selection.pads = editor.selection.pads?.filter(
      (p) => p.id != pad.id
    );
  });
}
</script>

<template>
  <pcb-entity-detail-container
    :title="'Pad - ID ' + props.pad.id"
    @delete="deletePad(props.pad)"
  >
    <base-form>
      <base-form-group label="Name">
        <input v-model="name" type="text" class="form-control" />
      </base-form-group>

      <base-form-group label="Network">
        <select v-model="network" class="form-select">
          <template v-for="item in editor.currentPcb?.networks" :key="item.id">
            <option :value="item">{{ item.name }}</option>
          </template>
          <option :value="null">None</option>
        </select>
      </base-form-group>

      <base-form-group label="Component">
        <select v-model="component" class="form-select">
          <template
            v-for="item in editor.currentPcb?.components"
            :key="item.id"
          >
            <option :value="item">{{ item.name }}</option>
          </template>
          <option :value="null">None</option>
        </select>
      </base-form-group>
    </base-form>
  </pcb-entity-detail-container>
</template>
