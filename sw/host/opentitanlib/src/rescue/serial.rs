// Copyright lowRISC contributors (OpenTitan project).
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0

use anyhow::Result;
use std::rc::Rc;
use std::time::Duration;

use crate::app::TransportWrapper;
use crate::io::uart::Uart;
use crate::rescue::xmodem::Xmodem;
use crate::rescue::{Rescue, RescueError, RescueMode};
use crate::uart::console::UartConsole;

pub struct RescueSerial {
    uart: Rc<dyn Uart>,
    reset_delay: Duration,
    enter_delay: Duration,
}

impl RescueSerial {
    const ONE_SECOND: Duration = Duration::from_secs(1);
    pub const REBOOT: RescueMode = RescueMode(u32::from_be_bytes(*b"REBO"));
    pub const BAUD: RescueMode = RescueMode(u32::from_be_bytes(*b"BAUD"));
    pub const WAIT: RescueMode = RescueMode(u32::from_be_bytes(*b"WAIT"));

    const BAUD_115K: [u8; 4] = *b"115K";
    const BAUD_230K: [u8; 4] = *b"230K";
    const BAUD_460K: [u8; 4] = *b"460K";
    const BAUD_921K: [u8; 4] = *b"921K";
    const BAUD_1M33: [u8; 4] = *b"1M33";
    const BAUD_1M50: [u8; 4] = *b"1M50";

    pub fn new(uart: Rc<dyn Uart>) -> Self {
        RescueSerial {
            uart,
            reset_delay: Duration::from_millis(50),
            enter_delay: Duration::from_secs(5),
        }
    }
}

impl Rescue for RescueSerial {
    fn enter(&self, transport: &TransportWrapper, reset_target: bool) -> Result<()> {
        log::info!("Setting serial break to trigger rescue mode.");
        self.uart.set_break(true)?;
        if reset_target {
            transport.reset_target(self.reset_delay, /*clear_uart=*/ true)?;
        }
        UartConsole::wait_for(&*self.uart, r"rescue:.*\r\n", self.enter_delay)?;
        log::info!("Rescue triggered. clearing serial break.");
        self.uart.set_break(false)?;
        // Upon entry, rescue is going to tell us what mode it is.
        // Consume and discard.
        let _ = UartConsole::wait_for(&*self.uart, r"(ok|error):.*\r\n", Self::ONE_SECOND);
        Ok(())
    }

    fn set_speed(&self, baud: u32) -> Result<()> {
        // Make sure the requested rate is a known rate.
        let symbol = match baud {
            115200 => Self::BAUD_115K,
            230400 => Self::BAUD_230K,
            460800 => Self::BAUD_460K,
            921600 => Self::BAUD_921K,
            1333333 => Self::BAUD_1M33,
            1500000 => Self::BAUD_1M50,
            _ => return Err(RescueError::BadMode(format!("Unsupported badrate {baud}")).into()),
        };

        // Request to change rates.
        self.set_mode(Self::BAUD)?;

        // Send the new rate and check for success.
        self.uart.write(&symbol)?;
        let result = UartConsole::wait_for(&*self.uart, r"(ok|error):.*\r\n", Self::ONE_SECOND)?;
        if result[1] == "error" {
            return Err(RescueError::BadMode(result[0].clone()).into());
        }
        // Change our side of the connection to the new rate.
        self.uart.set_baudrate(baud)?;
        Ok(())
    }

    fn set_mode(&self, mode: RescueMode) -> Result<()> {
        let mode = mode.0.to_be_bytes();
        self.uart.write(&mode)?;
        let enter = b'\r';
        self.uart.write(std::slice::from_ref(&enter))?;
        let mode = std::str::from_utf8(&mode)?;
        let result = UartConsole::wait_for(
            &*self.uart,
            &format!("mode: {mode}\r\n(ok|error):.*\r\n"),
            Self::ONE_SECOND,
        )?;

        if result[1] == "error" {
            return Err(RescueError::BadMode(result[0].clone()).into());
        }
        Ok(())
    }

    fn wait(&self) -> Result<()> {
        self.set_mode(Self::WAIT)?;
        Ok(())
    }

    fn reboot(&self) -> Result<()> {
        self.set_mode(Self::REBOOT)?;
        Ok(())
    }

    fn send(&self, data: &[u8]) -> Result<()> {
        let xm = Xmodem::new();
        xm.send(&*self.uart, data)?;
        Ok(())
    }

    fn recv(&self) -> Result<Vec<u8>> {
        let mut data = Vec::new();
        let xm = Xmodem::new();
        xm.receive(&*self.uart, &mut data)?;
        Ok(data)
    }
}
