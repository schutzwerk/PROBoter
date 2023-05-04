import axios from "axios";
import { backendConfig } from "@/globals";
import type { Component, Network, Pad, Pcb, Scan } from "@/models";

/********************************
 *
 * PCB operations
 *
 ********************************/
export default {
  async getPcbs(): Promise<Pcb[]> {
    return axios.get(backendConfig.pcbApi + "/pcb").then((response) =>
      response.data.map((element: Pcb) => {
        return {
          id: element.id,
          name: element.name,
          thickness: element.thickness,
          description: element.description,
          numScans: element.numScans,
          numComponents: element.numComponents,
          numNetworks: element.numNetworks,
          networks: [],
          components: [],
          pads: [],
          scans: [],
        };
      })
    );
  },

  async getPcbById(pcbId: number): Promise<Pcb> {
    return axios
      .get(backendConfig.pcbApi + "/pcb/" + pcbId)
      .then((response) => {
        const element = response.data;
        return {
          id: element.id,
          name: element.name,
          thickness: element.thickness,
          description: element.description,
          numScans: element.num_scans,
          numComponents: element.num_components,
          numNetworks: element.num_networks,
          networks: [],
          components: [],
          pads: [],
          scans: [],
        };
      });
  },

  async createPcb(
    name: string,
    description: string,
    thickness: number
  ): Promise<Pcb> {
    return axios
      .post(backendConfig.pcbApi + "/pcb", {
        name: name,
        description: description,
        thickness: thickness,
      })
      .then((response) => response.data);
  },

  async deletePcb(pcbId: number) {
    return axios
      .delete(backendConfig.pcbApi + "/pcb/" + pcbId)
      .then((response) => response.data);
  },

  getPcbPreviewUrl: function (pcbId: number) {
    return backendConfig.pcbApi + "/pcb/" + pcbId + "/preview";
  },

  async getPcbScans(pcbId: number) {
    return axios
      .get(backendConfig.pcbApi + "/pcb/" + pcbId + "/scan")
      .then((response) => response.data);
  },

  /********************************
   *
   * PCB scan operations
   *
   ********************************/
  async getScans(pcbId: number) {
    return axios
      .get(backendConfig.pcbApi + "/pcb/" + pcbId + "/scan")
      .then((response) => response.data);
  },

  getScanImageUrl(scan: Scan) {
    return (
      backendConfig.pcbApi +
      "/pcb/" +
      scan.pcbId +
      "/scan/" +
      scan.id +
      "/image"
    );
  },

  getScanPreviewUrl(scan: Scan) {
    return (
      backendConfig.pcbApi +
      "/pcb/" +
      scan.pcbId +
      "/scan/" +
      scan.id +
      "/preview"
    );
  },

  async loadScanImage(scan: Scan): Promise<Blob> {
    return axios
      .get(this.getScanImageUrl(scan), {
        responseType: "blob",
      })
      .then((response) => response.data);
  },

  async updateScan(scan: Scan): Promise<Scan> {
    return axios
      .put(
        backendConfig.pcbApi + "/pcb/" + scan.pcbId + "/scan/" + scan.id,
        scan
      )
      .then((response) => response.data);
  },

  async deleteScan(scan: Scan): Promise<null> {
    return axios.delete(
      backendConfig.pcbApi + "/pcb/" + scan.pcbId + "/scan/" + scan.id
    );
  },

  async importScan(pcb: Pcb, file: Blob | string) {
    const formData = new FormData();
    formData.append("scan-file", file);
    return axios
      .post(
        backendConfig.pcbApi + "/pcb/" + pcb.id + "/scan/import",
        formData,
        {
          headers: {
            "Content-Type": "application/zip",
          },
        }
      )
      .then((response) => response.data);
  },

  /********************************
   *
   * PCB component operations
   *
   ********************************/
  async getComponents(pcbId: number): Promise<Component[]> {
    return axios
      .get(backendConfig.pcbApi + "/pcb/" + pcbId + "/component")
      .then((response) => response.data);
  },

  async createComponent(
    pcbId: number,
    component: Component
  ): Promise<Component> {
    return axios
      .post(backendConfig.pcbApi + "/pcb/" + pcbId + "/component", {
        isVisible: component.isVisible,
        isTemporary: component.isTemporary,
        marking: component.marking,
        vendor: component.vendor,
        contour: component.contour,
      })
      .then((response) => response.data);
  },

  async updateComponent(component: Component): Promise<Component> {
    return axios
      .put(
        backendConfig.pcbApi +
          "/pcb/" +
          component.pcbId +
          "/component/" +
          component.id,
        component
      )
      .then((response) => response.data);
  },

  async deleteComponent(pcbId: number, componentId: number): Promise<void> {
    return axios.delete(
      backendConfig.pcbApi + "/pcb/" + pcbId + "/component/" + componentId
    );
  },

  /********************************
   *
   * PCB pin operations
   *
   ********************************/
  async getPins(pcbId: number) {
    return axios
      .get(backendConfig.pcbApi + "/pcb/" + pcbId + "/pin")
      .then((response) => response.data);
  },

  async createPin(pcbId: number, pad: Pad) {
    return axios
      .post(backendConfig.pcbApi + "/pcb/" + pcbId + "/pin", {
        isVisible: pad.isVisible,
        isTemporary: pad.isTemporary,
        networkId: pad.networkId,
        componentId: pad.componentId,
        center: pad.center,
      })
      .then((response) => response.data);
  },

  async updatePin(pin: Pad) {
    const newPin = JSON.parse(JSON.stringify(pin));
    if (newPin.name === null) {
      delete newPin.name;
    }
    return axios
      .put(
        backendConfig.pcbApi + "/pcb/" + pin.pcbId + "/pin/" + pin.id,
        newPin
      )
      .then((response) => response.data);
  },

  async deletePin(pcbId: number, pinId: number) {
    return axios
      .delete(backendConfig.pcbApi + "/pcb/" + pcbId + "/pin/" + pinId)
      .then((response) => response.data);
  },

  /********************************
   *
   * Electrical network operations
   *
   ********************************/
  async getNetworks(pcbId: number): Promise<Array<Network>> {
    return axios
      .get(backendConfig.pcbApi + "/pcb/" + pcbId + "/network")
      .then((response) => response.data);
  },

  async createNetwork(network: Network): Promise<Network> {
    return axios
      .post(backendConfig.pcbApi + "/pcb/" + network.pcbId + "/network", {
        name: network.name,
        isVisible: network.isVisible,
        isTemporary: network.isTemporary,
        pinIds: network.pinIds,
      })
      .then((response) => response.data);
  },

  async updateNetwork(network: Network): Promise<Network> {
    return axios
      .put(
        backendConfig.pcbApi +
          "/pcb/" +
          network.pcbId +
          "/network/" +
          network.id,
        network
      )
      .then((response) => response.data);
  },

  async deleteNetwork(pcbId: number, networkId: number): Promise<void> {
    return axios
      .delete(backendConfig.pcbApi + "/pcb/" + pcbId + "/network/" + networkId)
      .then((response) => response.data);
  },
};
