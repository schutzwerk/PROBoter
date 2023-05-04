import { usePcbEditorStore, type PcbEditorStore } from "@/stores/pcbEditor";
import type { Handler } from "./usePcbEventDispatcher";
import log from "js-vue-logger";
import pcbs from "@/api/pcbs";
import type { ProbingPlanePosition } from "@/stores/pcbEditor";

export default class ComponentCreateEventHandler implements Handler {
  public name = "COMPONENT_CREATE";

  private store: PcbEditorStore;
  private probingPlanePositions = new Array<ProbingPlanePosition>();

  constructor() {
    this.store = usePcbEditorStore();
  }

  activate() {
    log.info("[ComponentCreateEventHandler] activate");
    this.store.currentMode = this;
    this.store.statusBar = {
      text: "Select three or more points defining the componet contour",
      buttons: [
        {
          text: "",
          icon: "commit",
          variant: "primary",
          action: () => this.commitContour(),
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

  deactivate() {
    log.info("[ComponentCreateEventHandler] deactivate");
    this.cleanupTemporaryPads();
    this.store.currentMode = null;
    this.store.clearSelection();
    this.store.clearStatusBar();
  }

  cleanupTemporaryPads() {
    // remove temp pads
    this.store.currentPcb.pads = this.store.currentPcb.pads.filter(
      (p) => !p.isTemporary
    );
    this.probingPlanePositions = [];
  }

  commitContour() {
    if (this.probingPlanePositions.length >= 3) {
      pcbs
        .createComponent(this.store.currentPcbId, {
          contour: this.probingPlanePositions.map((p) => [p.x, p.y, p.z]),
          pcbId: this.store.currentPcbId,
          id: -1,
          name: "",
          vendor: "",
          marking: "",
          package: "UNKNOWN",
          isVisible: true,
          isTemporary: false,
        })
        .then((newComponent) => {
          log.debug("Successfully created component:", newComponent);
          this.store.currentPcb.components.push(newComponent);
          this.store.currentPcb.numComponents += 1;
        });
    }
    this.cleanupTemporaryPads();
  }

  async handle(type: string) {
    log.debug("[ComponentCreateEventHandler] handle", type);
    if (this.store.currentProbingPlanePosition != null) {
      // Add the selected point to the new component contour point list
      if (type === "click" || type == "touchstart") {
        log.debug("[ComponentCreateEventHandler] handle click");
        this.probingPlanePositions.push(this.store.currentProbingPlanePosition);

        this.store.currentPcb.pads.push({
          pcbId: this.store.currentPcbId,
          center: [
            this.store.currentProbingPlanePosition.x,
            this.store.currentProbingPlanePosition.y,
            this.store.currentProbingPlanePosition.z,
          ],
          componentId: 0,
          networkId: 0,
          isVisible: true,
          isTemporary: true,
          name: "",
          id: -1,
        });
      }
    }
  }
}
