<script setup lang="ts">
import { type PropType, computed } from "vue";

export interface SelectOption {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  value: any;
  text: string;
}

const props = defineProps({
  options: {
    type: Array as PropType<Array<SelectOption>>,
    default: () => [],
  },
  ariaLabel: {
    type: String,
    default: "",
  },
  modelValue: {
    type: [Object, String, Number, null] as PropType<
      object | string | number | null
    >,
    required: true,
  },
});

const currentIndex = computed(() => {
  let currentIdx = props.options.findIndex(
    (opt) => opt.value == props.modelValue
  );
  return currentIdx;
});

const emit = defineEmits(["update:modelValue"]);

function onInput(event: Event) {
  let input = event.target as HTMLSelectElement;
  emit("update:modelValue", props.options[Number(input.value)].value);
}
</script>

<template>
  <select
    class="form-select"
    :aria-label="props.ariaLabel"
    :value="currentIndex"
    @input="onInput"
  >
    <option v-for="(option, idx) in props.options" :key="idx" :value="idx">
      {{ option.text }}
    </option>
  </select>
</template>
