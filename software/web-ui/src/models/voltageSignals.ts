export interface VoltageMeasurement {
  pin: number;
  description: string;
  measurements: Array<number>;
  timeResolutionNanoseconds: number;
  startTime: Date;
}

export interface VoltageSignal {
  clock: number;
  data1: number;
  data2: number;
  control: number;
}

export interface BusProtocolRating {
  i2c: number;
  spi: number;
  uart: number;
  oneWire: number;
}

export interface VoltageSignalAnalysisResult {
  protocolName: string;
  signals: Array<VoltageSignal>;
  identificationRatings: BusProtocolRating;
}
