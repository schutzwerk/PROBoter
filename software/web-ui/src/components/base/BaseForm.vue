<script setup lang="ts"></script>

<template>
  <form>
    <slot></slot>

    <div class="row">
      <div class="col">
        <slot name="footer"></slot>
      </div>
    </div>
  </form>
</template>
