#include "../../inc/MarlinConfig.h"

#if ENABLED(PROBOTER) && ENABLED(USE_PROBOTER_TEST_PCB)

#include "../gcode.h"
#include "../../module/proboter.h"

/**
 * M371: Get test PCB status
 */
void GcodeSuite::M371() {
  int test_pad_status;
  Proboter::TestPCBStatus status;

  status = Proboter.get_test_pcb_status();

    SERIAL_ECHO("{");
    // The border pad status
    SERIAL_ECHO("\"border-pads\": ");
    SERIAL_ECHO(int(status.border_test_pads));
    SERIAL_ECHO(",");
    SERIAL_ECHO("\"tmp\": ");
    SERIAL_ECHO(status.test_pads);
    SERIAL_ECHO(",");

    // Write the main test pad stati
    SERIAL_ECHO("\"test-pads\": [");
    test_pad_status = status.test_pads;
    for(int i=0; i<PROBOTER_TEST_PCB_NUM_PADS; i++) {
      SERIAL_ECHO(1 & int(test_pad_status >> i));
      if(i < (PROBOTER_TEST_PCB_NUM_PADS - 1))
        SERIAL_ECHO(", ");
    }
    SERIAL_ECHO("]");
    SERIAL_ECHO("}");
    SERIAL_EOL();
}

#endif // PROBOTER && USE_PROBOTER_TEST_PCB
