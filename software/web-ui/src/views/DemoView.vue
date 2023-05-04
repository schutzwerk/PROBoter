<script setup lang="ts">
/**
 * Control of PROBoter demo modi
 */
import BasePage from "@/components/base/BasePage.vue";
import DemoProbeParty from "@/components/demo/DemoProbeParty.vue";
</script>

<template>
  <base-page :title="'Demo Mode'">
    <div class="row">
      <div class="col-xxl-3 col-xl-6">
        <demo-probe-party />
      </div>
    </div>
  </base-page>
</template>
