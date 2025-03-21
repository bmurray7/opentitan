// Copyright lowRISC contributors (OpenTitan project).
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0

#ifndef OPENTITAN_SW_DEVICE_SILICON_CREATOR_MANUF_BASE_FLASH_INFO_PERMISSIONS_H_
#define OPENTITAN_SW_DEVICE_SILICON_CREATOR_MANUF_BASE_FLASH_INFO_PERMISSIONS_H_

#include "sw/device/lib/dif/dif_flash_ctrl.h"

/**
 * Access permissions for flash info page 0 (holds device_id and manuf_state).
 *
 * We keep ECC disabled on this page as the ATE cannot use ECC when writing this
 * page earlier during the provisioning process.
 */
dif_flash_ctrl_region_properties_t kFlashInfoPage0Permissions = {
    .ecc_en = kMultiBitBool4False,
    .high_endurance_en = kMultiBitBool4False,
    .erase_en = kMultiBitBool4True,
    .prog_en = kMultiBitBool4True,
    .rd_en = kMultiBitBool4True,
    .scramble_en = kMultiBitBool4False};

/**
 * Access permissions for flash info page 3 (holds wafer_auth_secret).
 */
dif_flash_ctrl_region_properties_t kFlashInfoPage3WritePermissions = {
    .ecc_en = kMultiBitBool4True,
    .high_endurance_en = kMultiBitBool4False,
    .erase_en = kMultiBitBool4True,
    .prog_en = kMultiBitBool4True,
    .rd_en = kMultiBitBool4False,
    .scramble_en = kMultiBitBool4False};

/**
 * Access permissions for flash info page 4 (holds attestation key seeds).
 */
dif_flash_ctrl_region_properties_t kFlashInfoPage4Permissions = {
    .ecc_en = kMultiBitBool4True,
    .high_endurance_en = kMultiBitBool4False,
    .erase_en = kMultiBitBool4True,
    .prog_en = kMultiBitBool4True,
    .rd_en = kMultiBitBool4True,
    .scramble_en = kMultiBitBool4True};

#endif  // OPENTITAN_SW_DEVICE_SILICON_CREATOR_MANUF_BASE_FLASH_INFO_PERMISSIONS_H_
