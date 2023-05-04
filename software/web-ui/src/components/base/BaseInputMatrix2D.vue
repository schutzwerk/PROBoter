<script setup lang="ts">
/**
 * Component to edit a 2D matrix
 */
import { reactive, computed, type PropType } from "vue";
import log from "js-vue-logger";

const props = defineProps({
  modelValue: {
    type: Array as PropType<Array<Array<number>>>,
    required: true,
  },
  label: {
    type: String,
    default: null,
    required: false,
  },
  dimension: {
    type: Array as PropType<Array<number>>,
    default: () => [3, 3],
  },
  rows: {
    type: Number,
    default: 5,
  },
});

const state = reactive({
  valid: true as boolean,
  validationErrorText: undefined as undefined | string,
});

const emit = defineEmits(["update:modelValue"]);

const modelValueJson = computed(() => {
  return JSON.stringify(props.modelValue, null, " ");
});

const textareaClasses = computed(() => {
  let classes = ["form-control"];
  if (!state.valid) {
    classes.push("is-invalid");
  }
  return classes;
});

const isNumeric = (num: string | number) =>
  (typeof num === "number" || (typeof num === "string" && num.trim() !== "")) &&
  !isNaN(num as number);

function onValueChanged(event: Event) {
  let input = event.target as HTMLTextAreaElement;
  let valid = true;
  try {
    // Convert to JSON
    let parsedMat = JSON.parse(input.value);

    // Check for root level array
    if (!Array.isArray(parsedMat)) {
      state.valid = false;
      state.validationErrorText = "Input must be an array";
    }

    // Check outer dimension
    if ((parsedMat as Array<number>).length != props.dimension[0]) {
      state.valid = false;
      state.validationErrorText =
        "Outer dimension must be " + props.dimension[0];
      return;
    }

    // Ensure that the input is an array of arrays (2D matrix)
    parsedMat.forEach((element: Array<Array<number>>) => {
      if (!Array.isArray(element)) {
        valid = false;
        state.valid = false;
        state.validationErrorText = "Input must be an array of arrays";
      }
    });
    if (!valid) return;

    parsedMat.forEach((row: Array<number>) => {
      // Ensure that the inner dimensions match
      let rowArray = row as Array<number>;
      if (rowArray.length != props.dimension[1]) {
        valid = false;
        state.valid = false;
        state.validationErrorText =
          "Inner dimensions must be " + props.dimension[1];
        return;
      }

      // Ensure that the inner values are all numeric
      rowArray.forEach((col) => {
        if (!isNumeric(col)) {
          valid = false;
          state.valid = false;
          state.validationErrorText = "Elements must be all numeric";
          return;
        }
      });
    });
    if (!valid) return;

    state.valid = true;
    state.validationErrorText = undefined;
    log.debug("Validation success");
    emit("update:modelValue", parsedMat);
  } catch (e) {
    state.valid = false;
    state.validationErrorText = "Text is not valid JSON";
    log.debug("Invalid matrix 2D value");
  }
}
</script>

<template>
  <div>
    <label v-if="label" class="form-label">{{ label }}</label>
    <textarea
      :class="textareaClasses"
      :rows="props.rows"
      :value="modelValueJson"
      @input="onValueChanged($event)"
    ></textarea>
    <div v-if="!state.valid" class="invalid-feedback">
      {{ state.validationErrorText }}
    </div>
  </div>
</template>
