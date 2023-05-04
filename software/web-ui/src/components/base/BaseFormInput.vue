<script setup lang="ts">
import type { PropType } from "vue";

const props = defineProps({
  type: {
    type: String as PropType<"text" | "number">,
    default: "text",
  },
  placeholder: {
    type: String as PropType<string | undefined>,
    required: false,
    default: undefined,
  },
  modelValue: {
    type: [String, Number],
    required: true,
  },
  required: {
    type: Boolean,
  },
});

const emit = defineEmits(["update:modelValue"]);

const isNumeric = (num: string | number) =>
  (typeof num === "number" || (typeof num === "string" && num.trim() !== "")) &&
  !isNaN(num as number);

function onInput(event: Event) {
  let input = event.target as HTMLInputElement;
  if (props.type == "number") {
    if (isNumeric(input.value)) {
      emit("update:modelValue", Number(input.value));
    }
  } else {
    emit("update:modelValue", input.value);
  }
}
</script>

<template>
  <input
    id="{{ props.for }}"
    class="form-control"
    :type="props.type"
    :value="modelValue"
    :placeholder="props.placeholder"
    :required="props.required"
    @input="onInput($event)"
  />
</template>
