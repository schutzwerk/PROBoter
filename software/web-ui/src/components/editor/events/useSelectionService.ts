import log from "js-vue-logger";
import { usePcbEditorStore, type PcbEditorStore } from "@/stores/pcbEditor";
import type { Pad } from "@/models";

export interface PinSelection {
  cancelled: boolean;
  pins: Array<Pad>;
}

class SelectionService {
  /*
   * Global selection service
   */
  private store: PcbEditorStore;
  private static instance: SelectionService;
  private isFinished = false;
  private isCancelled = false;

  constructor() {
    this.store = usePcbEditorStore();
  }

  public static getInstance(): SelectionService {
    if (!SelectionService.instance) {
      SelectionService.instance = new SelectionService();
    }
    return SelectionService.instance;
  }

  async selectPin(): Promise<PinSelection> {
    return await this.selectPins(false);
  }

  commitSelection() {
    log.debug("Commiting selection");
    this.isFinished = true;
  }

  cancelSelection() {
    this.isCancelled = true;
  }

  async selectPins(
    multiple = false,
    text: string | null = null
  ): Promise<PinSelection> {
    this.isFinished = false;
    this.isCancelled = false;

    if (multiple) {
      this.store.statusBar = {
        text: text ? text : "Select pin(s)",
        buttons: [
          {
            text: "",
            icon: "commit",
            action: () => (this.isFinished = true),
            variant: "primary",
          },
        ],
      };
    }

    while (!this.isFinished && !this.isCancelled) {
      await this.sleep(1000);
      if (this.store.isSelectionEmpty === false) {
        if (this.store.selection.pads.length >= 1 && !multiple) {
          this.commitSelection();
        }
      }
    }
    log.info("Selection " + (this.isFinished ? "COMMITED" : "CANCELLED"));

    const userSelection: PinSelection = {
      cancelled: !this.isFinished,
      pins: [],
    };

    if (multiple) {
      userSelection.pins = this.store.selection.pads
        ? this.store.selection.pads
        : [];
    } else {
      userSelection.pins = this.store.selection.pads
        ? [this.store.selection.pads[0]]
        : [];
    }
    this.store.clearStatusBar();
    log.debug("Returning pin(s)", userSelection);
    return userSelection;
  }

  selectComponents() {
    return new Promise<void>((resolve) => {
      log.info("Selecting components");
      resolve();
    });
  }

  selectNetworks() {
    return new Promise<void>((resolve) => {
      log.info("Selecting networks");
      resolve();
    });
  }

  async selectEntities(
    entityFilter = { pins: true, components: true, networks: true }
  ) {
    console.log(entityFilter);
    if (entityFilter.pins) {
      return await this.selectPins();
    }
    if (entityFilter.components) {
      await this.selectComponents();
    }
    if (entityFilter.networks) {
      await this.selectNetworks();
    }
  }

  sleep(milliseconds: number) {
    return new Promise((resolve) => setTimeout(resolve, milliseconds));
  }
}

export const useSelectionService = function () {
  return SelectionService.getInstance();
};
