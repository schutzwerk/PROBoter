<script setup lang="ts">
/**
 * A modal component based on
 * Bootstrap
 */
import type { PropType } from "vue";
import { Modal } from "bootstrap";
import { onMounted, computed, ref } from "vue";

export type ModalSize = "sm" | "lg" | "xl" | null;

const props = defineProps({
  title: {
    type: String as PropType<string | null>,
    default: null,
  },
  size: {
    type: String as PropType<ModalSize>,
    default: null,
  },
});

const emit = defineEmits(["show", "shown", "hide", "hidden", "hidePrevented"]);

const modalClass = computed(() => {
  let modalClasses = ["modal", "fade"];
  if (props.size) modalClasses.push("modal-" + props.size);
  return modalClasses;
});

const modalContainer = ref<string | Element>("");

let modalObj: Modal | null = null;

onMounted(() => {
  modalObj = new Modal(modalContainer.value);
  const modalElem = modalContainer.value as Element;
  modalElem.addEventListener("show.bs.modal", (event) => emit("show", event));
  modalElem.addEventListener("shown.bs.modal", (event) => emit("shown", event));
  modalElem.addEventListener("hide.bs.modal", (event) => emit("hide", event));
  modalElem.addEventListener("hidden.bs.modal", (event) =>
    emit("hidden", event)
  );
  modalElem.addEventListener("hidePrevented.bs.modal", (event) =>
    emit("hidePrevented", event)
  );
});

function show() {
  modalObj?.show();
}

function hide() {
  modalObj?.hide();
}

function toggle() {
  console.log("Toggle modal");
  modalObj?.toggle();
  console.log("DONE");
}

defineExpose({
  show,
  hide,
  toggle,
});
</script>

<template>
  <div ref="modalContainer" :class="modalClass" tabindex="-1">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h2 v-if="props.title">{{ props.title }}</h2>
          <slot name="header"></slot>
          <button
            type="button"
            class="btn-close btn-close-white"
            data-bs-dismiss="modal"
            aria-label="Close"
          ></button>
        </div>
        <div class="modal-body">
          <slot></slot>
        </div>
        <div class="modal-footer">
          <slot name="footer"></slot>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@import "@/assets/style.scss";

.modal-content {
  color: $fg-04dp;
  background: $bg-04dp;
}

.modal-footer:empty {
  display: none;
}
</style>
