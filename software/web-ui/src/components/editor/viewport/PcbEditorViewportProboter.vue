<script setup lang="ts">
/**
 * Component to render a 3D model of the PROBoter hardware
 */
import Group from "@/plugins/threejs/components/Group.vue";
import PcbEditorViewportProboterProbe from "@/components/editor/viewport/PcbEditorViewportProboterProbe.vue";
</script>

<template>
  <group>
    <pcb-editor-viewport-proboter-probe :probe-type="'P1'" />
    <pcb-editor-viewport-proboter-probe :probe-type="'P11'" />
    <pcb-editor-viewport-proboter-probe :probe-type="'P2'" />
    <pcb-editor-viewport-proboter-probe :probe-type="'P21'" />
  </group>
</template>
