/**
 * Proboter.cpp
 */

#include "../inc/MarlinConfig.h"

#if ENABLED(PROBOTER)

  #include "proboter.h"
  #include "probe.h"
  #include "motion.h"
  #include "endstops.h"
  #include "planner.h"

  #define PROBOTER_PROBE_TRIGGERED() !READ(PROBOTER_PROBE_CENTERING_PIN)
  #define PROBOTER_PROBING_SPEED_MM_S PROBOTER_PROBING_SPEED / 60

  float Proboter::last_probed_z = 0;

  void Proboter::setup(){
    // Setup the probe centering input pin
    SET_INPUT_PULLUP(PROBOTER_PROBE_CENTERING_PIN);

    // Setup the test PCB input pins
    SET_INPUT_PULLDOWN(PROBOTER_TEST_PCB_PIN_TESTPADS);
    SET_INPUT_PULLDOWN(PROBOTER_TEST_PCB_PIN_DO);

    // Setup the test PCB output pins
    SET_OUTPUT(PROBOTER_TEST_PCB_PIN_SCLK);
    SET_OUTPUT(PROBOTER_TEST_PCB_PIN_LC);
    SET_OUTPUT(PROBOTER_TEST_PCB_PIN_OE);
    SET_OUTPUT(PROBOTER_TEST_PCB_PIN_PL);

    WRITE_PIN(PROBOTER_TEST_PCB_PIN_SCLK, LOW);
    WRITE_PIN(PROBOTER_TEST_PCB_PIN_LC, LOW);
    WRITE_PIN(PROBOTER_TEST_PCB_PIN_PL, HIGH);
    WRITE_PIN(PROBOTER_TEST_PCB_PIN_OE, LOW);
  }

  int Proboter::get_light_status() {
    #if ENABLED(PROBOTER_IS_LIGHT_CONTROLLER)
      return READ_PIN(PROBOTER_LIGHT_CONTROL_PIN);
    #else
      // No light control support
      return -1;
    #endif
  }

  void Proboter::set_light_intensity(byte intensity) {
    #if ENABLED(PROBOTER_IS_LIGHT_CONTROLLER)
    pinMode(PROBOTER_LIGHT_CONTROL_PIN, OUTPUT);
    extDigitalWrite(PROBOTER_LIGHT_CONTROL_PIN, intensity);
    analogWrite(PROBOTER_LIGHT_CONTROL_PIN, intensity);
    #endif
  }

  void Proboter::test_pcb_sclk_tick() {
    WRITE_PIN(PROBOTER_TEST_PCB_PIN_SCLK, HIGH);
    delay(1);
    WRITE_PIN(PROBOTER_TEST_PCB_PIN_SCLK, LOW);
    delay(1);
  }

  void Proboter::test_pcb_lc_tick(){
      WRITE_PIN(PROBOTER_TEST_PCB_PIN_LC, HIGH);
      delay(1);
      WRITE_PIN(PROBOTER_TEST_PCB_PIN_LC, LOW);
      delay(1);
  }

  void Proboter::test_pcb_sclk_lc_tick() {
    WRITE_PIN(PROBOTER_TEST_PCB_PIN_LC, HIGH);
    WRITE_PIN(PROBOTER_TEST_PCB_PIN_SCLK, HIGH);
    delay(1);
    WRITE_PIN(PROBOTER_TEST_PCB_PIN_LC, LOW);
    WRITE_PIN(PROBOTER_TEST_PCB_PIN_SCLK, LOW);
    delay(1);
  }

  Proboter::TestPCBStatus Proboter::get_test_pcb_status() {

    // Read the status of the border pads
    TestPCBStatus status = TestPCBStatus{0};
    status.border_test_pads = READ_PIN(PROBOTER_TEST_PCB_PIN_TESTPADS) & 0x1;

    // Read the values from the single test pads from the shift registers:

    // Reset the shift registers
    WRITE_PIN(PROBOTER_TEST_PCB_PIN_PL, LOW);
    WRITE_PIN(PROBOTER_TEST_PCB_PIN_OE, LOW);
    WRITE_PIN(PROBOTER_TEST_PCB_PIN_LC, LOW);
    WRITE_PIN(PROBOTER_TEST_PCB_PIN_SCLK, LOW);
    delay(1);
    test_pcb_sclk_lc_tick();
    
    // Load the current status in the data latch and shift registers
    test_pcb_lc_tick();

    // Start reading the current values from the shift registers
    WRITE_PIN(PROBOTER_TEST_PCB_PIN_PL, HIGH);
    delay(1);
    status.test_pads = 0;
    for(int i=0; i < PROBOTER_TEST_PCB_NUM_PADS; i++) {
      status.test_pads |= READ_PIN(PROBOTER_TEST_PCB_PIN_DO) << (PROBOTER_TEST_PCB_NUM_PADS - i);
      test_pcb_sclk_tick();
    }

    return status;
  }

  void Proboter::center_circle() {
    // Initial probing
    last_probed_z = 0.f;
    bool triggered = probe_z(Z_MAX_POS, -1, 1, PROBOTER_PROBING_SPEED_MM_S);
    float z0 = last_probed_z;
    float z0_cleared = z0 - PROBOTER_Z_CLEARANCE;

    if(!triggered) {
      SERIAL_ECHO_MSG(" ERROR: First probe not touched pin");
      return;
    }
    float p0[4];
    memcpy(p0, current_position, 4 * sizeof(float));

    // Probe 4 points (2 in each axis direction)
    //           x(0)
    //           |
    //   (3)x----|----x(2)
    //           |
    //           x(1)
    int i;
    float points[6][3];
    float step_dirs[6][2] = {
                              { PROBOTER_PROBING_STEP,  0.0},
                              {-1.0 * PROBOTER_PROBING_STEP,  0.0},
                              { 0.0,  PROBOTER_PROBING_STEP},
                              { 0.0, -1.0 * PROBOTER_PROBING_STEP},
                              { PROBOTER_PROBING_STEP,  0.0},
                              {-1.0 * PROBOTER_PROBING_STEP,  0.0},
                             };

    // The probing center is optimized during the probing process!
    float probing_center[4];
    memcpy(probing_center, p0, 4 * sizeof(float));
    for(i=0; i<6; i++) {
      // Move to initial point
      memcpy(current_position, probing_center, 4 * sizeof(float));
      line_to_current_position(PROBOTER_PROBING_SPEED_MM_S);
      probe_line(z0, 0.01, z0_cleared, step_dirs[i], points[i]);

      if(i==1) {
        // Adjust the probing center x coordinate
        probing_center[0] = (points[0][0] + points[1][0]) * 0.5;
      }
      if(i==3) {
        // Adjust the probing center y coordinate
        probing_center[1] = (points[2][1] + points[3][1]) * 0.5;
      }
    }

    // Write the results to the serial as JSON
    char pos_string[6];
    SERIAL_ECHO_MSG("calibration_points: [");
    for(i=2; i<6; i++) {
      snprintf(pos_string, sizeof(pos_string), "%.3f", points[i][0]);
      SERIAL_ECHO("{\"x\":");
      SERIAL_ECHO(pos_string);
      snprintf(pos_string, sizeof(pos_string), "%.3f", points[i][1]);
      SERIAL_ECHO(", \"y\":");
      SERIAL_ECHO(pos_string);
      snprintf(pos_string, sizeof(pos_string), "%.3f", points[i][2]);
      SERIAL_ECHO(", \"z\":");
      SERIAL_ECHO(pos_string);
      SERIAL_ECHOLNPGM("}");
      if(i < 5) SERIAL_ECHOLNPGM(", ");
    }
    SERIAL_ECHOLNPGM("]");
    SERIAL_EOL();
  }

  bool Proboter::probe_line(float init_z, float min_step, float z_retract, float (&direction)[2], float (&out_probe_point)[3]) {

    int step_counter = 0;
    float f = 1.0;
    bool triggered = true;
    bool last_triggered = true;
    while(step_counter < 20 && abs(f) >= min_step) {
      current_position[X_AXIS] += direction[0] * f;
      current_position[Y_AXIS] += direction[1] * f;
      //SERIAL_ECHOPAIR("Probing pos x:", pos_string);
      //SERIAL_ECHOPAIR("Probing pos y:", current_position[Y_AXIS]);
      //SERIAL_EOL();
      line_to_current_position(PROBOTER_PROBING_SPEED_MM_S);
      triggered = probe_z(init_z + 0.75, z_retract, -1, PROBOTER_PROBING_SPEED_MM_S);
      out_probe_point[0] = current_position[X_AXIS];
      out_probe_point[1] = current_position[Y_AXIS];
      out_probe_point[2] = last_probed_z;

      if(triggered != last_triggered) {
        // Edge transition
        // New step is in the other direction
        // and half the size
        f = -0.5 * f;
        step_counter = 0;
      } else {
        step_counter++;
      }
      last_triggered = triggered;
      //SERIAL_ECHOPAIR(" Z probed:", last_probed_z);
      //serialprintPGM(triggered ? "TOUCHED" : "NOT TOUCHED");
      //SERIAL_EOL();
    }

    return step_counter < 20;
  }

  bool Proboter::probe_z(float z_max, float z_retract, float z_clearance, float feed) {
      // Initiate the movement
      current_position[Z_AXIS] = z_max;
      line_to_current_position(PROBOTER_PROBING_SPEED_MM_S);

      // Lower probe until it is triggered or the max axis position is reached
      bool triggered = PROBOTER_PROBE_TRIGGERED();
      while((planner.has_blocks_queued() || planner.cleaning_buffer_counter) 
        && !triggered) {
          // Poll the probing pin
          triggered = PROBOTER_PROBE_TRIGGERED();
          if(triggered) {
            last_probed_z = planner.get_axis_position_mm(Z_AXIS);
          }
          idle();
      }

      // Stop the axis
      planner.quick_stop();
      planner.synchronize();

      // Resync the postion:
      // This step is very important to fix the
      // position difference in the planer and 
      // motion module after quick stopping!!
      set_current_from_steppers_for_axis(Z_AXIS);
      sync_plan_position();

      // Retracting
      if(z_retract >= 0) {
        // Retract to an absolute value
        current_position[Z_AXIS] = z_retract;
      } else {
        // Relative offset retract
        current_position[Z_AXIS] -= z_clearance;
      }
      line_to_current_position(PROBOTER_PROBING_SPEED_MM_S);
      planner.synchronize();

      return triggered;
  }

#endif // PROBOTER