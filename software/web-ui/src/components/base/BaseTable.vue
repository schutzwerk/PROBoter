<script setup lang="ts">
import type { PropType } from "vue";

export interface TableField {
  key: string;
  label: string;
}

// Allow explicit any type here because users can use arbitrary
// data for the selection
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Item = { [key: string]: any };
const props = defineProps({
  items: {
    type: Array as PropType<Array<Item>>,
    required: true,
  },
  fields: {
    type: Array as PropType<Array<TableField>>,
    required: true,
  },
});
</script>

<template>
  <table class="table">
    <thead>
      <tr>
        <th v-for="field in props.fields" :key="field.key">
          {{ field.label }}
        </th>
      </tr>
    </thead>

    <tbody>
      <tr v-for="(item, index) in props.items" :key="index">
        <td v-for="field in props.fields" :key="index + '-' + field.key">
          {{ item[field.key] }}
        </td>
      </tr>
    </tbody>
  </table>
</template>
