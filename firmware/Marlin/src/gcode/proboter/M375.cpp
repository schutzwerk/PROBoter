#include "../../inc/MarlinConfig.h"

#if ENABLED(PROBOTER)

#include "../gcode.h"
#include "../../module/proboter.h"

/**
 * M375: Get light status
 */
void GcodeSuite::M375() {
  int lightStatus;

  lightStatus = Proboter.get_light_status();
  SERIAL_ECHO(lightStatus);
  SERIAL_EOL();
}

#endif // PROBOTER
