/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "platform.h"

#include "config/config.h"
#include "drivers/osd.h"
#include "io/serial.h"
#include "osd/osd.h"
#include "pg/vcd.h"

void targetConfiguration(void)
{
    // Called for defaults, before saved user configuration is loaded at boot.
    // 2026.6.2's VTX_MSP_UART macro would overwrite FUNCTION_RX_SERIAL.
    serialPortConfig_t *receiver = serialFindPortConfigurationMutable(SERIALRX_UART);
    if (receiver) {
        receiver->functionMask = FUNCTION_RX_SERIAL | FUNCTION_VTX_MSP;
    }

    // Compiling HD support must not select an unconfigured HD port by default.
    vcdProfileMutable()->video_system = VIDEO_SYSTEM_AUTO;
    osdConfigMutable()->displayPortDevice = OSD_DISPLAYPORT_DEVICE_AUTO;
    osdConfigMutable()->canvas_cols = OSD_SD_COLS;
    osdConfigMutable()->canvas_rows = OSD_SD_ROWS;

    // Match the upstream SD defaults; its USE_OSD_HD reset otherwise puts
    // warnings and the horizon at HD coordinates on the analog display.
    osdElementConfig_t *elements = osdElementConfigMutable();
    for (int i = 0; i < OSD_ITEM_COUNT; i++) {
        elements->item_pos[i] = OSD_POS(10, 7);
    }
    uint16_t profiles = 0;
    for (unsigned i = 1; i <= OSD_PROFILE_COUNT; i++) {
        profiles |= OSD_PROFILE_FLAG(i);
    }
    elements->item_pos[OSD_WARNINGS] = OSD_POS(9, 10) | profiles;
    elements->item_pos[OSD_CROSSHAIRS] = OSD_POS(13, 6);
    elements->item_pos[OSD_ARTIFICIAL_HORIZON] = OSD_POS(14, 2);
    elements->item_pos[OSD_HORIZON_SIDEBARS] = OSD_POS(14, 6);
    elements->item_pos[OSD_CAMERA_FRAME] = OSD_POS(3, 1);
    elements->item_pos[OSD_UP_DOWN_REFERENCE] = OSD_POS(13, 6);
#ifdef USE_OSD_NAV_MAP
    elements->item_pos[OSD_NAV_MAP] = OSD_POS(1, 1);
#endif
}
