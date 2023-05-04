<script setup lang="ts">
import { type PropType, computed } from "vue";

export interface CheckGroupOption {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  value: any;
  text: string;
}

const props = defineProps({
  options: {
    type: Array as PropType<Array<CheckGroupOption>>,
    default: () => [],
  },
  ariaLabel: {
    type: String,
    default: "",
  },
  modelValue: {
    type: Array,
    required: true,
  },
});

const checked = computed(() => {
  let currentVals = props.options.map((opt) =>
    props.modelValue.includes(opt.value)
  );
  return currentVals;
});

const emit = defineEmits(["update:modelValue"]);

function onInput(event: Event) {
  let input = event.target as HTMLInputElement;
  let newSelection = props.options
    .filter((opt) => {
      if (opt.value == input.value) return input.checked;
      return props.modelValue.includes(opt.value);
    })
    .map((opt) => opt.value);
  emit("update:modelValue", newSelection);
}
</script>

<template>
  <div>
    <template v-for="(option, idx) in props.options" :key="idx">
      <div class="form-check form-check-inline">
        <input
          :id="'probe-select-' + idx"
          class="form-check-input"
          type="checkbox"
          :value="option.value"
          :checked="checked[idx]"
          @change="onInput($event)"
        />
        <label class="form-check-label" :for="'probe-select-' + idx">{{
          option.text
        }}</label>
      </div>
    </template>
  </div>
</template>
