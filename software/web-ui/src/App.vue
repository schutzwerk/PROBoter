<script setup lang="ts">
import { reactive, provide, ref } from "vue";
import { RouterLink, RouterView } from "vue-router";
import log from "js-vue-logger";

import BaseModal from "@/components/base/BaseModal.vue";
import TheNavigation from "@/components/TheNavigation.vue";
import TheProboterConnectionControl from "@/components/TheProboterConnectionControl.vue";

export interface MessageBox {
  confirm(
    message: string,
    title?: string,
    okTitle?: string,
    cancelTitle?: string
  ): Promise<boolean>;
}

const msgBox = ref();

type BooleanPromise = (value: boolean | Promise<boolean>) => void;
interface State {
  isNavbarExpanded: boolean;
  msgBoxResolve: BooleanPromise | null;
  msgBoxTitle: string;
  msgBoxMessage: string;
  msgBoxOkayTitle: string;
  msgBoxCancelTitle: string;
}

const state: State = reactive({
  isNavbarExpanded: false,
  msgBoxResolve: null,
  msgBoxTitle: "",
  msgBoxMessage: "",
  msgBoxOkayTitle: "Yes",
  msgBoxCancelTitle: "No",
});

function onNavbarClick() {
  log.debug("Navbar exansion toggled");
  state.isNavbarExpanded = !state.isNavbarExpanded;
}

function msgBoxConfirm(
  message: string,
  title = "",
  okTitle = "Yes",
  cancelTitle = "No"
): Promise<boolean> {
  log.info("[App] msgBoxConfirm", title, message);
  state.msgBoxTitle = title;
  state.msgBoxMessage = message;
  state.msgBoxOkayTitle = okTitle;
  state.msgBoxCancelTitle = cancelTitle;

  msgBox.value?.show();

  return new Promise((resolve) => {
    state.msgBoxResolve = resolve;
  });
}

function onConfirmMsgBox() {
  let resolve = state.msgBoxResolve;
  state.msgBoxResolve = null;
  msgBox.value?.hide();
  if (resolve) {
    resolve(true);
  }
}

function onDeclineMsgBox() {
  let resolve = state.msgBoxResolve;
  state.msgBoxResolve = null;
  msgBox.value?.hide();
  if (resolve) {
    resolve(false);
  }
}

function onMsgBoxClosed() {
  if (state.msgBoxResolve) {
    state.msgBoxResolve(false);
    state.msgBoxResolve = null;
  }
}

provide<MessageBox>("messageBox", { confirm: msgBoxConfirm });
</script>

<template>
  <div id="app-container">
    <!-- The global MessageBox instance -->
    <base-modal ref="msgBox" :title="state.msgBoxTitle" @hide="onMsgBoxClosed">
      {{ state.msgBoxMessage }}
      <template #footer>
        <button class="btn btn-secondary" @click="onDeclineMsgBox">
          {{ state.msgBoxCancelTitle }}
        </button>
        <button class="btn btn-primary" @click="onConfirmMsgBox">
          {{ state.msgBoxOkayTitle }}
        </button>
      </template>
    </base-modal>

    <!--Navbar at the top of the page visible in all screen sizes
                smaller than extra large-->
    <nav class="navbar navbar-dark d-xl-none">
      <a class="navbar-brand" :to="{ name: 'home' }">PROBoter</a>
      <button
        class="navbar-toggler"
        type="button"
        data-bs-toggle="collapse"
        data-bs-target="#navbarSupportedContent"
        aria-controls="navbarSupportedContent"
        aria-expanded="false"
        aria-label="Toggle navigation"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div id="navbarSupportedContent" class="collapse navbar-collapse">
        <TheNavigation />
      </div>
    </nav>

    <!-- Wrapper for the side-by-side sidebar and content layout -->
    <div id="wrapper">
      <!-- The navigation sidebar visible on extra large displays only -->
      <div
        id="sidebar"
        class="dp-04 d-md-none d-sm-none d-none d-lg-none d-xl-flex"
        :class="{ expanded: state.isNavbarExpanded }"
        @click="onNavbarClick"
      >
        <nav class="navbar vertical">
          <RouterLink
            class="navbar-brand w-100 mb-3"
            :to="{ name: 'home' }"
            @click.stop
          >
            <img class="logo" src="/images/logo_cropped.png" />
          </RouterLink>
          <TheNavigation />
        </nav>
        <TheProboterConnectionControl :tiny="!state.isNavbarExpanded" />
      </div>
    </div>

    <!-- Actual content -->
    <div id="content">
      <RouterView />
    </div>
  </div>
</template>

<style lang="scss">
@import "@/assets/style.scss";

#app {
  display: flex;
  flex-flow: column;
  align-items: stretch;
  height: 100vh;
  padding: 0;
}

#wrapper {
  display: flex;
  flex-flow: row;
  width: 100%;
  flex: 1;
}

#sidebar {
  width: 60px;
  padding: 10px;
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  display: flex;
  flex-flow: column;
  overflow-x: hidden;
  transition: width 0.5s;
  z-index: 1000;
}

#sidebar.expanded {
  width: 250px;
}

#sidebar .navbar {
  background-color: transparent;
}

#content {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 60px;
  right: 0;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  flex-flow: row;
  align-items: stretch;
}

@media (max-width: map-get($grid-breakpoints, "xl")) {
  #content {
    left: 0;
    top: 56px;
  }
}

.navbar-brand > span {
  display: inline-block;
  overflow-x: hidden;
}

.logo {
  height: 2em;
}

.backend-connection-control {
  margin-top: auto;
}
</style>
