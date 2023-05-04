import { usePcbEditorStore, type PcbEditorStore } from "@/stores/pcbEditor";
import { usePcbStore, type PcbStore } from "@/stores/pcbs";
import type { Handler } from "./usePcbEventDispatcher";
import log from "js-vue-logger";

export default class NetworkCreateEventHandler implements Handler {
  public name = "NETWORK_CREATE";

  private store: PcbEditorStore;
  private pcbs: PcbStore;

  constructor() {
    this.store = usePcbEditorStore();
    this.pcbs = usePcbStore();
  }

  activate() {
    log.info("[NetworkCreateEventHandler] activate");
    this.store.currentMode = this;
    this.store.statusBar = {
      text: "Select two or more pins defining the electrical network",
      buttons: [
        {
          text: "",
          icon: "commit",
          variant: "primary",
          action: () => this.commitNetwork(),
        },
        {
          text: "",
          icon: "cancel",
          variant: "secondary",
          action: () => this.deactivate(),
        },
      ],
    };
  }

  commitNetwork() {
    if (this.store.selection.pads.length >= 2) {
      const pinIds = this.store.selection.pads.map((pin) => pin.id);
      this.pcbs
        .createNetwork({
          id: -1,
          pcbId: this.store.currentPcbId,
          name: "Newnet",
          pinIds: pinIds,
          isVisible: true,
          isTemporary: false,
        })
        .finally(() => {
          this.store.clearSelection();
        });
    }
  }

  deactivate() {
    log.info("[NetworkCreateEventHandler] deactivate");
    this.store.currentMode = null;
    this.store.clearSelection();
    this.store.clearStatusBar();
  }

  async handle() {
    // Nothing to do here
    log.info("[NetworkCreateEventHandler] handle");
  }
}
