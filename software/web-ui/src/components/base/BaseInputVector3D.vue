<script setup lang="ts">
/**
 * Component to edit a 3D vector
 */
import type { PropType } from "vue";

const props = defineProps({
  modelValue: {
    type: Object as PropType<[number, number, number]>,
    required: true,
  },
  label: {
    type: String,
    default: null,
    required: false,
  },
  xLabel: {
    type: String,
    default: "X",
  },
  yLabel: {
    type: String,
    default: "Y",
  },
  zLabel: {
    type: String,
    default: "Z",
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update:modelValue"]);

const isNumeric = (num: string | number) =>
  (typeof num === "number" || (typeof num === "string" && num.trim() !== "")) &&
  !isNaN(num as number);

function onValueChanged(index: number, event: Event) {
  let input = event.target as HTMLInputElement;
  if (isNumeric(input.value)) {
    emit(
      "update:modelValue",
      props.modelValue.map((v, i) => (i == index ? Number(input.value) : v))
    );
  }
}
</script>

<template>
  <div v-if="modelValue != null">
    <label v-if="label" class="form-label">{{ label }}</label>
    <div class="input-group">
      <!-- X -->
      <span class="input-group-text">{{ xLabel }}</span>
      <input
        type="text"
        class="form-control"
        :value="modelValue[0]"
        :disabled="props.disabled"
        number
        @input.prevent="onValueChanged(0, $event)"
      />
      <!-- Y -->
      <span class="input-group-text">{{ yLabel }}</span>
      <input
        type="text"
        class="form-control"
        :value="modelValue[1]"
        :disabled="props.disabled"
        number
        @input.prevent="onValueChanged(1, $event)"
      />
      <!-- Z -->
      <span class="input-group-text">{{ zLabel }}</span>
      <input
        type="text"
        class="form-control"
        :value="modelValue[2]"
        :disabled="props.disabled"
        number
        @input.prevent="onValueChanged(2, $event)"
      />
      <slot></slot>
    </div>
  </div>
</template>
