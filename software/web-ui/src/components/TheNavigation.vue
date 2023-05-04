<script setup lang="ts">
import { RouterLink } from "vue-router";
import { BIconBalloon, BIconCpu, BIconGear } from "bootstrap-icons-vue";
</script>

<template>
  <div class="nav-container">
    <ul class="navbar-nav">
      <li class="nav-item mb-2 side-nav">
        <RouterLink
          class="nav-link"
          :to="{ name: 'pcb-index' }"
          title="PCBs"
          @click.stop
        >
          <span class="nav-icon">
            <BIconCpu />
          </span>
          PCBs
        </RouterLink>
      </li>
      <li class="nav-item mb-2 side-nav" :to="{ name: 'proboter-control' }">
        <RouterLink
          class="nav-link"
          to="/proboter"
          title="Hardware Control"
          @click.stop
        >
          <span class="nav-icon">
            <BIconGear />
          </span>
          Hardware
        </RouterLink>
      </li>

      <li class="nav-item mb-2 side-nav">
        <RouterLink
          class="nav-link"
          :to="{ name: 'demo-mode' }"
          title="Demo Mode"
          @click.stop
        >
          <span class="nav-icon">
            <BIconBalloon />
          </span>
          Demo Mode
        </RouterLink>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.nav-container {
  width: 100%;
}

.nav-item {
  max-width: 100%;
  width: 100%;
  white-space: nowrap;
  text-align: left;
}

.nav-icon {
  width: 20px;
  text-align: center;
  margin-right: 20px;
}

.navbar-nav .nav-link {
  overflow-x: hidden;
  max-width: 100%;
  padding: 4px 11px;
}
</style>
