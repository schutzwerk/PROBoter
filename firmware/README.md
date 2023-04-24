# PROBoter firmware

This folder contains the firmware running on the four [BIGTREETECH SKR V1.3](https://github.com/bigtreetech/BIGTREETECH-SKR-V1.3) controller boards driving the PROBoter hardware platform. The code is basically a fork of the popular 3D printer firmware [Marlin](https://marlinfw.org/) with some additional PROBoter-specific configurations and G-Code extensions.

## PROBoter-specifc modifications
The code is a fork of Marlin's [bugfix-2.1.x branch](https://github.com/MarlinFirmware/Marlin/tree/bugfix-2.1.x) with some PROBoter-specific modifications described below.

### Hardware configuration
The firmware is configured for the following hardware installed in the hardware prototype of the PROBoter:
- Board: [BIGTREETECH SKR V1.3](https://github.com/bigtreetech/BIGTREETECH-SKR-V1.3) 
- Stepper driver: [Trinamics TMC2130](https://www.trinamic.com/products/integrated-circuits/details/tmc2130/)
- Mechanical transmission: Tooth belt (GT2 profile), 16 teeth pulley in all axes

Additional settings like homing directions, motor / drive and endstop configuration is done on a per-probe basis. Therefore, the firmware must be built individually **for each controller board**!

### Additional G-Codes
- **M370** Perform circle centering of a single electrical probe. This routine is used during hardware calibration and described in the [original PROBoter thesis](https://github.com/schutzwerk/PROBoter/blob/master/publications/PROBoter_thesis.pdf).
- **M371** Read the status of a custom evaluation board (currently not in use).
- **M375** Set light intensity. This command is only executed by the board which is configured as light controller.
- **M376** Read the currently set light intensity.


## Building the firmware
The firmware can be easily built using [PlatformIO](https://platformio.org/).

First install PlatformIO using pip:
```
pip install platformio
```

Select the probe / controller board by uncommenting the respective line in [Configuration.h](./Marlin/Configuration.h).

Example configuration to build the firmware for probe 1:
```c
// @section PROBoter-specific configuration

// Enable PROBoter-specific functionality
#define PROBOTER

// Select the probe for which the firmware should be built
// !! Only select ONE probe at a time !!
#define PROBE_1
//#define PROBE_11
//#define PROBE_2
//#define PROBE_21
```

Finally, compile and upload the firmware to the controller board:
```
pio run -t upload
```

After a board reset the new firmware can be used :)
