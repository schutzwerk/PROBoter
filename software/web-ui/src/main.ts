import { createApp } from "vue";
import { createPinia } from "pinia";
import logger from "js-vue-logger";
import App from "./App.vue";
import router from "./router";
import "bootstrap";
import { backendConfig, devBackendConfig, prodBackendConfig } from "./globals";

if (import.meta.env.PROD) {
  Object.assign(backendConfig, prodBackendConfig);
}

if (import.meta.env.DEV) {
  Object.assign(backendConfig, devBackendConfig);
}

console.log(backendConfig);

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

app.mount("#app");

logger.useDefaults();
logger.setLevel(logger.DEBUG);
