<script setup lang="ts">
import type { PropType } from "vue";

interface DropdownOption {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  value: any;
  text: string;
}

const props = defineProps({
  options: {
    type: Array as PropType<Array<DropdownOption>>,
    default: () => [],
  },
  modelValue: {
    type: Object,
    required: true,
  },
});

defineEmits(["update:modelValue"]);
</script>

<template>
  <div class="btn-group">
    <button type="button" class="btn btn-secondary">
      <slot></slot>
    </button>
    <button
      type="button"
      class="btn btn-secondary dropdown-toggle dropdown-toggle-split"
      data-bs-toggle="dropdown"
      aria-expanded="false"
    >
      <slot name="split-button"></slot>
      <span class="visually-hidden">Toggle Dropdown</span>
    </button>
    <ul class="dropdown-menu">
      <li
        v-for="option in props.options"
        :key="option.value"
        :value="option.value"
      >
        <a
          class="dropdown-item"
          @click.prevent="$emit('update:modelValue', option.value)"
        >
          {{ option.text }}</a
        >
      </li>
    </ul>
  </div>
</template>
