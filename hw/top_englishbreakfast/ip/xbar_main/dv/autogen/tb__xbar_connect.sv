// Copyright lowRISC contributors (OpenTitan project).
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0
//
// tb__xbar_connect generated by `tlgen.py` tool

xbar_main dut();

`DRIVE_CLK(clk_main_i)
`DRIVE_CLK(clk_fixed_i)

initial force dut.clk_main_i = clk_main_i;
initial force dut.clk_fixed_i = clk_fixed_i;

// TODO, all resets tie together
initial force dut.rst_main_ni = rst_n;
initial force dut.rst_fixed_ni = rst_n;

// Host TileLink interface connections
`CONNECT_TL_HOST_IF(rv_core_ibex__corei, dut, clk_main_i, rst_n)
`CONNECT_TL_HOST_IF(rv_core_ibex__cored, dut, clk_main_i, rst_n)

// Device TileLink interface connections
`CONNECT_TL_DEVICE_IF(rom_ctrl__rom, dut, clk_main_i, rst_n)
`CONNECT_TL_DEVICE_IF(rom_ctrl__regs, dut, clk_main_i, rst_n)
`CONNECT_TL_DEVICE_IF(peri, dut, clk_fixed_i, rst_n)
`CONNECT_TL_DEVICE_IF(flash_ctrl__core, dut, clk_main_i, rst_n)
`CONNECT_TL_DEVICE_IF(flash_ctrl__prim, dut, clk_main_i, rst_n)
`CONNECT_TL_DEVICE_IF(flash_ctrl__mem, dut, clk_main_i, rst_n)
`CONNECT_TL_DEVICE_IF(aes, dut, clk_main_i, rst_n)
`CONNECT_TL_DEVICE_IF(rv_plic, dut, clk_main_i, rst_n)
`CONNECT_TL_DEVICE_IF(rv_core_ibex__cfg, dut, clk_main_i, rst_n)
`CONNECT_TL_DEVICE_IF(sram_ctrl_main__regs, dut, clk_main_i, rst_n)
`CONNECT_TL_DEVICE_IF(sram_ctrl_main__ram, dut, clk_main_i, rst_n)
