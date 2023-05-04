<script setup lang="ts">
/**
 * Layout container for low level control elements
 * of a single PROBoter hardware entity
 */
import type { PropType } from "vue";
import { computed } from "vue";

export interface EntityStatus {
  title: string;
  variant: "okay" | "warning" | "error";
}

const props = defineProps({
  title: {
    type: String as PropType<string | null>,
    default: null,
  },
  status: {
    type: Object as PropType<EntityStatus | null>,
    default: null,
  },
});

const badgeVariant = computed(() => {
  switch (props.status?.variant) {
    case "okay":
      return "success";
    case "warning":
      return "warning";
    default:
      return "danger";
  }
});
</script>

<template>
  <div class="card bg-dark text-white">
    <div class="card-header">
      <div class="row">
        <!-- Entity name / title -->
        <div class="col">
          <div class="clearfix">
            <slot name="title">
              <h5 class="d-inline-block me-4">{{ props.title }}</h5>
            </slot>
            <!-- Entity status badge-->
            <slot name="status">
              <span
                style="margin-top: auto; margin-bottom: auto"
                :class="['badge', 'rounded-pill', 'bg-' + badgeVariant]"
              >
                <div>{{ props.status?.title }}</div>
              </span>
            </slot>
            <!-- Additional controls container-->
            <form class="d-inline-block float-end">
              <slot name="controls"></slot>
            </form>
          </div>
        </div>
      </div>
    </div>
    <div class="card-body">
      <!-- Main controls-->
      <slot></slot>
    </div>
  </div>
</template>
