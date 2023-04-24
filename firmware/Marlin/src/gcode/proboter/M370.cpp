#include "../../inc/MarlinConfig.h"

#if ENABLED(PROBOTER)

#include "../gcode.h"
#include "../../module/planner.h"
#include "../../module/proboter.h"

/**
 * M370: 4 point circle centering
 */
void GcodeSuite::M370() {
  Proboter.center_circle();
}

#endif // PROBOTER
