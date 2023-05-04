import { defineStore } from "pinia";
import { usePcbStore } from "@/stores/pcbs";
import type { Component, Pad, Network, Pcb, Scan } from "@/models";

export interface Selection {
  pads: Array<Pad>;
  components: Array<Component>;
  networks: Array<Network>;
  scans: Array<Scan>;
}

export interface SelectionUpdate {
  pads?: Array<Pad>;
  components?: Array<Component>;
  networks?: Array<Network>;
  scans?: Array<Scan>;
}

export interface ProbingPlanePosition {
  x: number;
  y: number;
  z: number;
}

export interface StatusBarButton {
  text: string;
  action: () => void;
  variant: "primary" | "secondary";
  icon: "commit" | "cancel" | null;
}

export interface StatusBar {
  text: string;
  buttons: Array<StatusBarButton>;
}

export interface Handler {
  activate(): void;
  deactivate(): void;
  handle(type: string, event: MouseEvent | TouchEvent): void;
}

export interface PcbEditorStore {
  currentPcbId: number;
  backgroundColor: number;
  isGridVisible: boolean;
  probingAreaColor: number;
  renderOrderProbingArea: number;
  renderOrderProbingAreaGrid: number;
  renderOrderPcbScans: number;
  renderOrderPcbComponents: number;
  renderOrderPcbPins: number;
  renderOrderPcbNetworks: number;
  currentProbingPlanePosition: ProbingPlanePosition | null;
  probingPlaneZ: number;
  currentMode: Handler | null;
  isProboterVisible: boolean;
  viewMode: string;
  statusBar: StatusBar;
  selection: Selection;
  isSelectionEmpty: boolean;

  currentPcb: Pcb;
  clearStatusBar(): void;
  clearSelection(): void;
}

export const usePcbEditorStore = defineStore("pcbEditor", {
  state: () => ({
    // ID of the currently edited PCB
    currentPcbId: 0 as number,

    // Background color of the PCB editor
    backgroundColor: 0x121212,
    // Whether the probing area grid is visible
    isGridVisible: true,
    // Color of the visible probing area / plane
    probingAreaColor: 0xf2f2f2,
    // Render order of PCB editor entities
    renderOrderProbingArea: 1,
    renderOrderProbingAreaGrid: 3,
    renderOrderPcbScans: 2,
    renderOrderPcbComponents: 4,
    renderOrderPcbPins: 6,
    renderOrderPcbNetworks: 5,

    // Current position on the probing plane
    currentProbingPlanePosition: { x: 0, y: 0, z: 0 } as ProbingPlanePosition,
    // Z offset of the current probing plane
    probingPlaneZ: 0,
    // Current operating mode
    currentMode: null as Handler | null,
    // Whether the PROBoter model is visibles
    isProboterVisible: false,
    // Current view mode: Possible values 2D or 3D
    viewMode: "2D",
    // Text displayed in the status bar
    statusBar: { text: "", buttons: [] as Array<StatusBarButton> },

    // The current editor selection
    selection: {
      pads: [] as Array<Pad>,
      components: [] as Array<Component>,
      networks: [] as Array<Network>,
      scans: [] as Array<Scan>,
    } as Selection,
  }),

  getters: {
    currentPcb(): Pcb {
      const pcbs = usePcbStore();
      return pcbs.getPcbById(this.currentPcbId) as Pcb;
    },
    isSelectionEmpty: (state) => {
      return (
        state.selection.pads.length == 0 &&
        state.selection.components.length == 0 &&
        state.selection.networks.length == 0 &&
        state.selection.scans.length == 0
      );
    },
    isPadSelected: (state) => {
      return (pad: Pad) =>
        state.selection.pads.find((p) => p.id === pad.id) !== undefined;
    },
    isComponentSelected: (state) => {
      return (component: Component) =>
        state.selection.components.find((comp) => comp.id === component.id) !==
        undefined;
    },
    isNetworkSelected: (state) => {
      return (network: Network) =>
        state.selection.networks.find((net) => net.id === network.id) !==
        undefined;
    },
    isScanSelected: (state) => {
      return (scan: Scan) =>
        state.selection.scans.find((tmp) => tmp.id === scan.id) !== undefined;
    },
  },

  actions: {
    clearStatusBar() {
      this.statusBar = { text: "", buttons: [] };
    },
    select(selection: SelectionUpdate) {
      this.clearSelection();
      if (selection.pads) {
        this.selection.pads = selection.pads;
      }
      if (selection.components) {
        this.selection.components = selection.components;
      }
      if (selection.networks) {
        this.selection.networks = selection.networks;
      }
      if (selection.scans) {
        this.selection.scans = selection.scans;
      }
    },
    clearSelection() {
      this.selection = {
        pads: [],
        components: [],
        networks: [],
        scans: [],
      };
    },

    setVisibility(entities: Selection, visible: boolean) {
      const pcbs = usePcbStore();
      if (entities.pads) {
        this.currentPcb?.pads.forEach((pad) => {
          if (entities.pads?.find((tmpPad) => tmpPad.id === pad.id)) {
            pad.isVisible = visible;
            pcbs.updatePad(pad);
          }
        });
      }

      if (entities.components) {
        this.currentPcb?.components.forEach((comp) => {
          if (entities.components?.find((tmpComp) => tmpComp.id === comp.id)) {
            comp.isVisible = visible;
            pcbs.updateComponent(comp);
          }
        });
      }

      if (entities.networks) {
        this.currentPcb?.networks.forEach((net) => {
          if (entities.networks?.find((tmpNet) => tmpNet.id === net.id)) {
            net.isVisible = visible;
            pcbs.updateNetwork(net);
          }
        });
      }
    },
    toggleVisibility(entities: SelectionUpdate) {
      const pcbs = usePcbStore();
      if (entities.pads) {
        this.currentPcb?.pads.forEach((pad) => {
          if (entities.pads?.find((tmpPad) => tmpPad.id === pad.id)) {
            pad.isVisible = !pad.isVisible;
            pcbs.updatePad(pad);
          }
        });
      }

      if (entities.components) {
        this.currentPcb?.components.forEach((comp) => {
          if (entities.components?.find((tmpComp) => tmpComp.id === comp.id)) {
            comp.isVisible = !comp.isVisible;
            pcbs.updateComponent(comp);
          }
        });
      }

      if (entities.networks) {
        this.currentPcb?.networks.forEach((net) => {
          if (entities.networks?.find((tmpNet) => tmpNet.id === net.id)) {
            net.isVisible = !net.isVisible;
            pcbs.updateNetwork(net);
          }
        });
      }

      if (entities.scans) {
        this.currentPcb?.scans.forEach((scan) => {
          if (entities.scans?.find((tmpScan) => tmpScan.id === scan.id)) {
            scan.isVisible = !scan.isVisible;
          }
        });
      }
    },
  },
});
