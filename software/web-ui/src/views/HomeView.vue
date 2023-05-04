<template>
  <div class="landingpage">
    <div class="heading mb-8">
      <img class="logo mb-4" src="/images/logo.png" />
      <h5 style="font-style: italic">
        Your handy embedded system pentesting
        <span style="font-weight: bold">PROB</span>
        <span>ing rob</span>
        <span style="font-weight: bold">ot(er)</span>
      </h5>
    </div>

    <div class="demo-wrapper">
      <img class="demo" src="/images/proboter_small.png" />
    </div>
  </div>
</template>

<style scoped>
.landingpage {
  flex: 1;
  display: flex;
  flex-flow: column;
  align-items: stretch;
  padding: 0.5em;
  text-align: center;
}

.heading {
  margin-bottom: 2rem;
}

.logo {
  height: 10em;
}

.demo-wrapper {
  align-items: center;
}

.demo {
  max-width: 600px;
  border-radius: 50%;
}
</style>
