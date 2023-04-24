#include "../../inc/MarlinConfig.h"

#if ENABLED(PROBOTER)

#include "../gcode.h"
#include "../../module/proboter.h"

/**
 * M376: Set light intensity
 */
void GcodeSuite::M376() {
  uint8_t intensity;

  if (!parser.seenval('I')) return;
  intensity = parser.value_byte();
  Proboter.set_light_intensity(intensity);
}

#endif // PROBOTER
