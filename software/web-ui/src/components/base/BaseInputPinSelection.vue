<script setup lang="ts">
/**
 * An UI element that allows interactive selection of one
 * or multiple pins / pads
 */
import { computed, reactive, ref, type PropType } from "vue";
import { BIconEyeFill } from "bootstrap-icons-vue";
import log from "js-vue-logger";

import BaseButton from "./BaseButton.vue";
import BaseFormInputGroup from "./BaseFormInputGroup.vue";
import { useSelectionService } from "../editor/events/useSelectionService";
import { usePcbEditorStore, type PcbEditorStore } from "@/stores/pcbEditor";
import type { Selection } from "@/stores/pcbEditor";
import type { Pad } from "@/models";

const store: PcbEditorStore = usePcbEditorStore();

let savedSelection: Selection;

const props = defineProps({
  modelValue: {
    type: Object as PropType<Array<Pad> | Pad | null>,
    default: null,
  },
  multiSelection: {
    type: Boolean,
    default: false,
  },
});

const input = ref();
const highlight = ref<InstanceType<typeof BaseButton>>();
const emit = defineEmits(["update:modelValue"]);

const entityText = computed(() => {
  /* 
  It is currently unclear what is returned if multiselection is enabled.
  For now we assume we always get an array of Pad. Therefore, an empty array would mean nothing is selected.
  */
  if (Array.isArray(props.modelValue)) {
    // Empty array -> No pins selected
    if (props.modelValue.length < 1) {
      return "No pins selected";
    }
    // Non-empty array -> We have one or more pins selected
    else {
      return props.modelValue.length + " pin(s) selected";
    }
  }
  // Not an array -> Single pin
  else {
    // Null -> No pin selected
    if (!props.modelValue) {
      return "No pin selected";
    } else {
      return "Pin (ID=" + props.modelValue.id + ")";
    }
  }
});

const data = reactive({
  highlightButtonSelected: false,
});

const state = () => {
  if (Array.isArray(props.modelValue)) {
    return props.modelValue.length > 0;
  } else {
    return props.modelValue !== null;
  }
};

const selectionService = useSelectionService();

async function startSelection() {
  // Save the current selection
  savedSelection = store.selection;
  log.debug("Saving current selection:", savedSelection);

  // Remove the focus from the 'select' button to allow the keyboard
  // triggers for selection commitment and cancellation to trigger
  input.value.focus();

  // Select pin(s)
  store.clearSelection();

  store.statusBar.text = "Select pins. Commit with ENTER.";

  let newSelection = await selectionService.selectPins(props.multiSelection);

  log.debug("Selection changed " + newSelection);

  emit(
    "update:modelValue",
    props.multiSelection
      ? newSelection.pins
      : newSelection.pins.length > 0
      ? newSelection.pins[0]
      : null
  );

  // Restore the old selection
  log.debug("Restoring previous selection");
  store.clearSelection();
  store.clearStatusBar();
  store.selection = savedSelection;
}

function highlightSelection() {
  // Start highlighting
  if (!data.highlightButtonSelected) {
    data.highlightButtonSelected = true;
    savedSelection = store.selection;
    store.clearSelection();

    // Multi pin
    if (Array.isArray(props.modelValue)) {
      store.selection.pads = props.modelValue;
    }
    // Single pin
    else {
      // Only add value if it is defined.
      if (props.modelValue) {
        store.selection.pads = [props.modelValue];
      } else {
        store.statusBar.text = "No pins selected";
        data.highlightButtonSelected = false;
        setTimeout(() => store.clearStatusBar(), 2000);
      }
    }
  }
  // Stop highlighting
  else {
    data.highlightButtonSelected = false;
    store.selection = savedSelection;
    store.clearStatusBar();
  }
}
</script>

<template>
  <base-form-input-group>
    <input
      ref="input"
      type="text"
      class="form-control"
      readonly
      :state="state"
      :value="entityText"
    />
    <base-button type="button" @click="startSelection">Select</base-button>
    <base-button
      ref="highlight"
      type="button"
      :variant="data.highlightButtonSelected ? 'primary' : 'secondary'"
      style="font-size: 0.8em"
      title="Highlight selection"
      @click="highlightSelection"
    >
      <b-icon-eye-fill />
    </base-button>
  </base-form-input-group>
</template>
