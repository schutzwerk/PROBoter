import axios from "axios";
import { backendConfig } from "@/globals";
import type { VoltageMeasurement, VoltageSignalAnalysisResult } from "@/models";

/********************************
 *
 * Voltage signal analysis operations
 *
 ********************************/
export default {
  async analyseVoltageSignals(
    voltageMeasurements: Array<VoltageMeasurement>
  ): Promise<Array<VoltageSignalAnalysisResult>> {
    // Convert the voltage signals
    const analysisInputs = voltageMeasurements.map((measurement) => {
      return {
        index: measurement.pin,
        source_name: measurement.description,
        voltage_levels: measurement.measurements,
        measurement_resolution: measurement.timeResolutionNanoseconds,
        start_time: measurement.startTime.toString(),
      };
    });
    // Trigger the voltage signal analysis
    return axios
      .post(backendConfig.signalAnalysisApi + "/analysis/", analysisInputs)
      .then((response) => response.data);
  },
};
