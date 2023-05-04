<script setup lang="ts">
/**
 * Component to edit a 2D vector
 */
const props = defineProps({
  modelValue: {
    type: Array,
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
        number
        @input="onValueChanged(0, $event)"
      />
      <!-- Y -->
      <span class="input-group-text">{{ yLabel }}</span>
      <input
        type="text"
        class="form-control"
        :value="modelValue[1]"
        number
        @input="onValueChanged(1, $event)"
      />
    </div>
  </div>
</template>
