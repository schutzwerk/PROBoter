import { defineStore } from "pinia";
import log from "js-vue-logger";

import { pcbApi } from "@/api";
import type { Pcb, Component, Pad, Network, Scan } from "@/models";

export type PcbStore = {
  pcbs: Array<Pcb>;
  createNetwork(network: Network): Promise<Network>;
};

export const usePcbStore = defineStore("pcbs", {
  state: () => ({
    pcbs: [] as Array<Pcb>,
  }),

  getters: {
    getPcbById() {
      return (pcbId: number): Pcb | undefined =>
        this.pcbs.find((pcb) => pcb.id === pcbId);
    },
    getComponentPins() {
      return (component: Component | undefined) => {
        if (!component) return [];
        const pcb = this.getPcbById(component.pcbId);
        if (!pcb) {
          return [];
        }
        return pcb.pads.filter((pin) => pin.componentId === component.id);
      };
    },
    getNetworkPins() {
      return (network: Network) => {
        const pcb = this.getPcbById(network.pcbId);
        if (!pcb) {
          return [];
        }
        return pcb.pads.filter((pad) => network.pinIds.includes(pad.id));
      };
    },
    getPcbPadById() {
      return (pcbId: number, pinId: number): Pad | null => {
        const currentPcb = this.getPcbById(pcbId);

        const retValue = currentPcb?.pads.find((i) => i.id === pinId);

        return retValue === undefined ? null : retValue;
      };
    },
  },

  actions: {
    /******************************************
     *
     * PCB actions
     *
     ******************************************/
    async fetchPcbs() {
      log.info("[PcbStore] Fetching PCBs from backend");
      return pcbApi.getPcbs().then((pcbs) => {
        log.debug("[PcbStore] Fetched " + pcbs.length + " PCB(s) from backend");
        this.pcbs = pcbs;
      });
    },

    async fetchPcbById(pcbId: number): Promise<Pcb | undefined> {
      // Trigger fetch from backend
      log.info(
        "[PcbStore] Fetching PCB metadata with ID " + pcbId + " from backend"
      );
      return pcbApi
        .getPcbById(pcbId)
        .then((pcb) => {
          log.debug("[PcbStore] PCB metadata successfully fetched");
          const pcbIdx = this.pcbs.findIndex((p) => p.id == pcbId);
          if (pcbIdx >= 0) {
            // Replace already fetched PCB
            this.pcbs[pcbIdx] = pcb;
          } else {
            // Add newly fetched PCB
            this.pcbs.push(pcb);
          }
          return pcb;
        })
        .then((pcb) => {
          log.info("[PcbStore] Fetching PCB details");
          return Promise.all([
            pcbApi.getComponents(pcb.id),
            pcbApi.getPins(pcb.id),
            pcbApi.getNetworks(pcb.id),
            pcbApi.getScans(pcb.id),
          ]).then((details) => {
            this.pcbs.forEach((tmpPcb, idx) => {
              if (tmpPcb.id === pcbId) {
                this.pcbs[idx].components = details[0];
                this.pcbs[idx].pads = details[1];
                this.pcbs[idx].networks = details[2];
                this.pcbs[idx].scans = details[3];
              }
            });
            return this.pcbs.find((pcb) => pcb.id === pcbId);
          });
        });
    },

    async createPcb(
      name: string,
      description: string,
      thickness: number
    ): Promise<Pcb> {
      log.info("[PcbStore] Creating new PCB");
      return pcbApi.createPcb(name, description, thickness).then((pcb) => {
        log.debug("[PcbStore] Successfully created PCB");
        this.pcbs.push(pcb);
        return pcb;
      });
    },

    async deletePcb(pcbId: number): Promise<void> {
      log.info("[PcbStore] Deleting PCB with ID " + pcbId);
      return pcbApi.deletePcb(pcbId).then(() => {
        this.pcbs = this.pcbs.filter((pcb) => pcb.id != pcbId);
        log.debug("[PcbStore] Successfully deleted PCB");
      });
    },

    async syncPcbScans(pcb: Pcb): Promise<void> {
      return pcbApi.getScans(pcb.id).then((pcbScans) => {
        this.pcbs.forEach((tmpPcb, idx) => {
          if (tmpPcb.id === pcb.id) {
            this.pcbs[idx].scans = pcbScans;
          }
        });
      });
    },

    /******************************************
     *
     * Pad actions
     *
     ******************************************/
    async createPad(pcb: Pcb, pad: Pad): Promise<Pad> {
      log.info("[PcbStore] Creating pad");
      return pcbApi.createPin(pcb.id, pad).then((newPin) => {
        pcb?.pads.push(newPin);
        return newPin;
      });
    },

    async updatePad(pad: Pad): Promise<Pad> {
      log.info("[PcbStore] Updating pad with ID " + pad.id);
      // Find the corresponding PCB
      const pcb = this.pcbs.find((pcb) => pcb.id === pad.pcbId);
      if (!pcb) throw new Error("PCB for pad not found!");

      pcbApi.updatePin(pad).then((updatedPin) => {
        pad = updatedPin;

        pcb.pads.forEach((tmpPad, idx) => {
          if (tmpPad.id === pad.id) {
            pcb.pads[idx] = pad;
          }
        });
        log.debug("[PcbStore] Successfully updated Pad.");
      });

      // Return the updated pad
      return new Promise((resolve) => resolve(pad));
    },

    async deletePad(pad: Pad): Promise<Pad> {
      log.info("[PcbStore] Deleting pad with ID " + pad.id);
      // Find the corresponding PCB
      const pcb = this.pcbs.find((pcb) => pcb.id === pad.pcbId);
      if (!pcb) throw new Error("PCB for pad not found!");

      pcbApi.deletePin(pad.pcbId, pad.id).then(() => {
        pcb.pads = pcb.pads.filter((p) => p.id != pad.id);
        log.debug("[PcbStore] Successfully deleted Pad.");
      });

      // Return the deleted pad
      return new Promise((resolve) => resolve(pad));
    },

    /******************************************
     *
     * Component actions
     *
     ******************************************/
    async createComponent(pcb: Pcb, component: Component): Promise<Component> {
      log.info("[PcbStore] Creating new component");
      return pcbApi.createComponent(pcb.id, component).then((newComponent) => {
        log.debug("Successfully created component:", newComponent);
        pcb.components.push(newComponent);
        pcb.numComponents += 1;
        return newComponent;
      });
    },

    async updateComponent(component: Component): Promise<Component> {
      log.info("[PcbStore] Updating component with ID " + component.id);
      // Find the corresponding PCB
      const pcb = this.pcbs.find((pcb) => pcb.id === component.pcbId);
      if (!pcb) throw new Error("PCB for component not found!");

      pcbApi.updateComponent(component).then((updatedComponent) => {
        component = updatedComponent;
        pcb.components.forEach((tmpComponent, idx) => {
          if (tmpComponent.id === component.id) {
            pcb.components[idx] = component;
          }
        });
      });

      // Return the deleted component
      return new Promise((resolve) => resolve(component));
    },

    async deleteComponent(component: Component): Promise<Component> {
      log.info("[PcbStore] Deleting component with ID " + component.id);
      // Find the corresponding PCB
      const pcb = this.pcbs.find((pcb) => pcb.id === component.pcbId);
      if (!pcb) throw new Error("PCB for component not found!");

      pcbApi.deleteComponent(component.pcbId, component.id).then(() => {
        pcb.components = pcb.components.filter((c) => c.id != component.id);
        log.debug("[PcbStore] Successfully deleted Component.");
      });

      // Return the updated component
      return new Promise((resolve) => resolve(component));
    },

    /******************************************
     *
     * Network actions
     *
     ******************************************/
    async createNetwork(network: Network): Promise<Network> {
      log.info("[PcbStore] Creating new network");
      // Find the corresponding PCB
      const pcb = this.pcbs.find((pcb) => pcb.id === network.pcbId);
      if (!pcb) throw new Error("PCB for network not found!");

      pcbApi.createNetwork(network).then((newNetwork) => {
        pcb.networks.push(newNetwork);
      });

      // Return the updated network
      return new Promise((resolve) => resolve(network));
    },

    async updateNetwork(network: Network): Promise<Network> {
      log.info("[PcbStore] Updating network with ID " + network.id);
      // Find the corresponding PCB
      const pcb = this.pcbs.find((pcb) => pcb.id === network.pcbId);
      if (!pcb) throw new Error("PCB for network not found!");

      pcbApi.updateNetwork(network).then((updatedNetwork) => {
        network = updatedNetwork;
        pcb.networks.forEach((tmpNet, idx) => {
          if (tmpNet.id === network.id) {
            pcb.networks[idx] = network;
          }
        });
      });

      // Return the updated network
      return new Promise((resolve) => resolve(network));
    },
    async deleteNetwork(network: Network): Promise<Network> {
      log.info("[PcbStore] Deleting network with ID " + network.id);
      // Find the corresponding PCB
      const pcb = this.pcbs.find((pcb) => pcb.id === network.pcbId);
      if (!pcb) throw new Error("PCB for network not found!");

      pcbApi.deleteNetwork(network.pcbId, network.id).then(() => {
        pcb.networks = pcb.networks.filter((n) => n.id != network.id);
        log.debug("[PcbStore] Successfully deleted Network.");
      });

      // Return the deleted Network
      return new Promise((resolve) => resolve(network));
    },

    /******************************************
     *
     * Scan actions
     *
     ******************************************/
    async updateScan(scan: Scan): Promise<Scan> {
      log.info("[PcbStore] Updating scan with ID " + scan.id);
      // Find the corresponding PCB
      const pcb = this.pcbs.find((pcb) => pcb.id === scan.pcbId);
      if (!pcb) throw new Error("PCB for network not found!");

      return pcbApi.updateScan(scan).then((updatedScan) => {
        pcb.scans.forEach((tmpNet, idx) => {
          if (tmpNet.id === updatedScan.id) {
            pcb.scans[idx] = updatedScan;
          }
        });
        return updatedScan;
      });
    },

    async deleteScan(scan: Scan): Promise<Scan> {
      log.info("[PcbStore] Deleting scan with ID " + scan.id);
      // Find the corresponding PCB
      const pcb = this.pcbs.find((pcb) => pcb.id === scan.pcbId);
      if (!pcb) throw new Error("PCB for scan not found!");

      return pcbApi.deleteScan(scan).then(() => {
        pcb.scans = pcb.scans.filter((n) => n.id != scan.id);
        log.debug("[PcbStore] Successfully deleted scan");
        return scan;
      });
    },

    async loadScanImage(scan: Scan): Promise<Blob> {
      // TODO Implement image data caching here!
      return pcbApi.loadScanImage(scan);
    },
  },
});
