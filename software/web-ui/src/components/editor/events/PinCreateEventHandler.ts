import log from "js-vue-logger";
import pcbs from "@/api/pcbs";
import { usePcbEditorStore, type PcbEditorStore } from "@/stores/pcbEditor";
import type { Handler } from "./usePcbEventDispatcher";

export default class PinCreateEventHandler implements Handler {
  public name = "PIN_CREATE";

  private store: PcbEditorStore;

  constructor() {
    this.store = usePcbEditorStore();
  }

  activate() {
    log.info("[PinCreatEventHandler] activate");
    this.store.currentMode = this;
    this.store.statusBar = {
      text: "Click on the probing area to create new pins.",
      buttons: [
        {
          text: "",
          icon: "cancel",
          variant: "secondary",
          action: () => this.deactivate(),
        },
      ],
    };
  }

  deactivate() {
    log.info("[PinCreatEventHandler] deactivate");
    this.store.currentMode = null;
    this.store.clearStatusBar();
  }

  handle(type: string) {
    if (
      this.store.currentProbingPlanePosition != null &&
      (type === "click" || type == "touchstart")
    ) {
      log.debug("Creating pin", this.store.currentProbingPlanePosition);
      pcbs
        .createPin(this.store.currentPcbId, {
          id: -1,
          name: "",
          center: [
            this.store.currentProbingPlanePosition.x,
            this.store.currentProbingPlanePosition.y,
            this.store.currentProbingPlanePosition.z,
          ],
          pcbId: this.store.currentPcbId,
          componentId: undefined,
          networkId: undefined,
          isVisible: true,
          isTemporary: false,
        })
        .then((newPin) => {
          log.debug("Created pin:", newPin);
          this.store.currentPcb.pads.push(newPin);
        });
    }
  }
}
