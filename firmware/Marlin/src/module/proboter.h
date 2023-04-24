/**
*
 */
#pragma once

/**
 * Proboter.h - manages PROBOter-specific tasks
 */

#include "../inc/MarlinConfig.h"
#include <stdint.h>

#if ENABLED(PROBOTER)

class Proboter {

  public:
    struct TestPCBStatus
    {
      bool border_test_pads : 1;
      int test_pads : 32;
    };
    
  private:
    static float last_probed_z;
    static bool probe_line(float init_z, float min_step, float z_retract, float (&direction)[2], float (&out_probe_point)[3]);
    static bool probe_z(float z_max, float z_retract, float z_clearance, float feed);

    // Legacy methods to debug the evaluation PCB
    static void test_pcb_sclk_tick();
    static void test_pcb_lc_tick();
    static void test_pcb_sclk_lc_tick();

  public:
    static void setup();

    static int get_light_status();
    static void set_light_intensity(uint8_t intensity);

    static void center_circle();
    static TestPCBStatus get_test_pcb_status();

};

extern Proboter Proboter;

#endif // PROBOTER
