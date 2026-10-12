/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once

// OpenAIO-Whoop rev1, tested against Betaflight 2026.6.2.
#define FC_TARGET_MCU RP2350A
#define BOARD_NAME OPENAIO_WHOOP
#define MANUFACTURER_ID FOSS
#define USE_TARGET_CONFIG

// The PCB placement is unfinished. A build must state its intended orientation;
// neither an old placement nor the parked footprint defines the finished board.
#ifdef USE_CONFIG
#ifndef OPENAIO_GYRO_ALIGN
#error "Define OPENAIO_GYRO_ALIGN after establishing the IMU placement."
#endif
#ifndef OPENAIO_BOARD_YAW
#error "Define OPENAIO_BOARD_YAW for the intended board mounting."
#endif
#endif
#define GYRO_1_ALIGN OPENAIO_GYRO_ALIGN
#define DEFAULT_ALIGN_BOARD_YAW OPENAIO_BOARD_YAW

// Fitted BMI270, four-wire SPI with 3.3V I/O and a separate 1.8V core supply.
#define USE_GYRO
#define USE_ACC
#define USE_ACCGYRO_BMI270
#define SPI1_SCK_PIN PA14
#define SPI1_SDI_PIN PA12
#define SPI1_SDO_PIN PA11
#define GYRO_1_SPI_INSTANCE SPI1
#define GYRO_1_CS_PIN PA15
#define GYRO_1_EXTI_PIN PA10

// Only enable this for an ICM-42688-P assembly with its matching bypass parts.
#ifdef OPENAIO_IMU_ICM42688P
#undef USE_ACCGYRO_BMI270
#define USE_GYRO_SPI_ICM42688P
#define USE_ACC_SPI_ICM42688P
#define USE_GYRO_CLKIN
#define GYRO_1_CLKIN_PIN PA13
#endif

// Puya PY25Q128HA, 16MB, JEDEC 0x852018. This is separate from the boot flash.
#define USE_FLASH
#define USE_FLASH_M25P16
#define USE_BLACKBOX
#define SPI0_SCK_PIN PA2
#define SPI0_SDI_PIN PA0
#define SPI0_SDO_PIN PA3
#define FLASH_SPI_INSTANCE SPI0
#define FLASH_CS_PIN PA1
#define DEFAULT_BLACKBOX_DEVICE BLACKBOX_DEVICE_FLASH

// Bluejay EFM8BB51, one bidirectional DShot state machine per motor on PIO0.
#define MOTOR1_PIN PA7
#define MOTOR2_PIN PA6
#define MOTOR3_PIN PA5
#define MOTOR4_PIN PA4
#define DEFAULT_MOTOR_DSHOT_SPEED PWM_TYPE_DSHOT600
#define DEFAULT_DSHOT_TELEMETRY DSHOT_TELEMETRY_ON
#define PIO_DSHOT_INDEX 0

// UART0 is the onboard ExpressLRS receiver. UART1 goes to the HD video pads.
#define UART0_TX_PIN PA16
#define UART0_RX_PIN PA17
#define UART1_TX_PIN PA24
#define UART1_RX_PIN PA25
#define USE_SERIALRX
#define USE_SERIALRX_CRSF
#define USE_TELEMETRY
#define USE_TELEMETRY_CRSF
#define DEFAULT_RX_FEATURE FEATURE_RX_SERIAL
#define SERIALRX_PROVIDER SERIALRX_CRSF
#define SERIALRX_UART SERIAL_PORT_UART0
#define USE_VTX
#define USE_VTX_MSP
// config.c adds VTX_MSP to the RX mask without the 2026.6.2 assignment conflict.
// Do not define VTX_MSP_UART or MSP_DISPLAYPORT_UART for the analog default.

// Q28 is absent. GPIO19 high permits analog VTX power, low forces it off.
// Inverted PINIO: logical inactive = high; logical active = analog off.
// This signal does not switch the always-powered VHD supply pad.
#define USE_PINIO
#define PINIO1_PIN PA19
#define PINIO1_CONFIG 129

// Both display implementations are present; config.c defaults to analog AUTO.
#define USE_OSD_SD
#define USE_OSD_HD
#define DEFAULT_FEATURES (FEATURE_OSD | FEATURE_TELEMETRY)
#define ENABLE_FB_OSD 1
#define OSD_W_PIN PA21
#define OSD_EN_PIN PA22
#define OSD_SYNC_PIN PA23
#define PIO_OSD_INDEX 2
#define OSD_FB_PICO_FLASH_FONT
#define OSD_FB_PICO_ENABLE_PIXEL_MODE 1
#define OSD_FB_PICO_POSTPROCESS 2
#define OSD_FB_ENABLE_SMALLFONT 1
#define OSD_BATTERY_PERCENT_WITH_SYMBOL
#define OSD_RSSI_WITH_SYMBOL
#define OSD_FRAMERATE_MAX_HZ 100
#define OSD_FRAMERATE_DEFAULT_HZ 50
#define OSD_DRAWSCREEN_TIME_LIMIT_US 20

// Keep LED strip instructions away from the 31-instruction OSD program.
#define USE_LED_STRIP
#define LED_STRIP_PIN PA18
#define PIO_LEDSTRIP_INDEX 1
#define LED0_PIN PA8
#define LED1_PIN PA9
#define USE_BEEPER
#define BEEPER_PIN PA20
#define BEEPER_INVERTED

#define ADC_VBAT_PIN PA27
#define ADC_CURR_PIN PA26
#define DEFAULT_VOLTAGE_METER_SOURCE VOLTAGE_METER_ADC
#define DEFAULT_CURRENT_METER_SOURCE CURRENT_METER_ADC
#define DEFAULT_VOLTAGE_METER_SCALE 200
#define DEFAULT_VOLTAGE_METER_DIVIDER 100
#define DEFAULT_CURRENT_METER_SCALE 500
