import axios from "axios";
import { backendConfig } from "@/globals";
import type {
  PinDetector,
  ComponentDetector,
  PcbVisualAnalysisResult,
} from "@/models";

/********************************
 *
 * Visual PCB analysis operations
 *
 ********************************/
export default {
  async analysePcbImage(
    image: File,
    chipDetectorId: string,
    pinDetectorId: string | null
  ): Promise<PcbVisualAnalysisResult> {
    const formData = new FormData();
    formData.append("pcb-image", image);
    formData.append("chip-detector", chipDetectorId);
    if (pinDetectorId !== null) {
      formData.append("pin-detector", pinDetectorId);
    }
    const response = await axios.post(
      backendConfig.pcbAnalysisApi + "/analysis",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  async getPinDetectors(): Promise<PinDetector[]> {
    return axios
      .get(backendConfig.pcbAnalysisApi + "/detectors/pin")
      .then((response) => response.data);
  },

  async getChipDetectors(): Promise<ComponentDetector[]> {
    return axios
      .get(backendConfig.pcbAnalysisApi + "/detectors/chip")
      .then((response) => response.data);
  },
};
