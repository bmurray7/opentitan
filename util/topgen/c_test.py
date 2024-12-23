# Copyright lowRISC contributors (OpenTitan project).
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0
"""This contains a class which is used to help generate top level SW tests.

We maintain as a separate class rather than merge implementation with c.py,
because both serve different purposes and need to capture the information
differently.
"""

import logging as log
import sys
from typing import Dict

from reggen.ip_block import IpBlock
from reggen.interrupt import IntrType

from .c import TopGenC
from .lib import find_module, Name


class TestPeripheral:
    """Captures a peripheral instance's attributes for use in SW tests.

    It encapsulates the settings for each peripheral's instance in the design.
    These settings are captured as identifiers that are already defined in
    other autogenerated / hand-edited sources such as top_{name}.h and the DIF
    headers, rather than hard-coded constants. This is done to ensure that a
    single source of truth is referenced in all of the tests.
    """
    def __init__(self, name: str, inst_name: str, base_addr_name: str):
        self.name = name
        self.inst_name = inst_name
        self.base_addr_name = base_addr_name


class IrqTestPeripheral(TestPeripheral):
    """Captures a peripheral instance's attributes for use in IRQ test."""
    def __init__(self, name: str, inst_name: str, base_addr_name: str,
                 plic_name: str, start_irq: str, end_irq: str,
                 plic_start_irq: str, status_type_mask: int,
                 status_default_mask: int):
        super().__init__(name, inst_name, base_addr_name)
        self.plic_name = plic_name
        self.start_irq = start_irq
        self.end_irq = end_irq
        self.plic_start_irq = plic_start_irq
        self.status_type_mask = status_type_mask
        self.status_default_mask = status_default_mask


class AlertTestPeripheral(TestPeripheral):
    """Captures a peripheral instance's attributes for use in IRQ test."""
    def __init__(self, name: str, inst_name: str, base_addr_name: str,
                 top_alert_name: str, dif_alert_name: str, num_alerts: int):
        super().__init__(name, inst_name, base_addr_name)
        self.top_alert_name = top_alert_name
        self.dif_alert_name = dif_alert_name
        self.num_alerts = num_alerts


class TopGenCTest(TopGenC):
    def __init__(self, top_info, name_to_block: Dict[str, IpBlock]):
        super().__init__(top_info, name_to_block)

        self.irq_peripherals = self._get_irq_peripherals()
        # Only generate alert_handler and mappings if there is an alert_handler
        if find_module(self.top['module'], 'alert_handler'):
            self.alert_peripherals = self._get_alert_peripherals()

    def _get_irq_peripherals(self):
        irq_peripherals = []
        self.devices()
        for entry in self.top['module']:
            inst_name = entry['name']
            if inst_name not in self.top["interrupt_module"]:
                continue

            name = entry['type']
            plic_name = (self._top_name + Name(["plic", "peripheral"]) +
                         Name.from_snake_case(inst_name))
            plic_name = plic_name.as_c_enum()

            # Device regions may have multiple TL interfaces. Pick the region
            # associated with the 'core' interface.
            if_name = 'core'
            if len(self.device_regions[inst_name]) == 1:
                if_name = list(self.device_regions[inst_name].keys())[0]
            try:
                region = self.device_regions[inst_name][if_name]
            except KeyError:
                log.error(f"The 'base_addrs' dict for {name} needs to have "
                          "one entry keyed with 'None' or 'core'.")
                sys.exit(1)

            base_addr_name = region.base_addr_name().as_c_define()

            plic_name = (self._top_name + Name(["plic", "peripheral"]) +
                         Name.from_snake_case(inst_name))
            plic_name = plic_name.as_c_enum()

            start_irq = self.device_irqs[inst_name][0]
            end_irq = self.device_irqs[inst_name][-1]
            plic_start_irq = (self._top_name + Name(["plic", "irq", "id"]) +
                              Name.from_snake_case(start_irq))
            plic_start_irq = plic_start_irq.as_c_enum()

            # Get DIF compliant, instance-agnostic IRQ names.
            start_irq = start_irq.replace(inst_name, f"dif_{name}_irq", 1)
            start_irq = Name.from_snake_case(start_irq).as_c_enum()
            end_irq = end_irq.replace(inst_name, f"dif_{name}_irq", 1)
            end_irq = Name.from_snake_case(end_irq).as_c_enum()

            # Create two sets of masks:
            # - status_type_mask encodes whether an IRQ is of status type
            # - status_default_mask encodes default of status type IRQ
            n = 0
            status_type_mask = 0
            status_default_mask = 0
            for irq in self.top["interrupt"]:
                if irq["module_name"] == inst_name:
                    if irq["intr_type"] == IntrType.Status:
                        setbit = (((1 << irq["width"]) - 1) << n)
                        status_type_mask |= setbit
                        if irq["default_val"] is True:
                            status_default_mask |= setbit
                    n += irq["width"]

            irq_peripheral = IrqTestPeripheral(name, inst_name, base_addr_name,
                                               plic_name, start_irq, end_irq,
                                               plic_start_irq, status_type_mask,
                                               status_default_mask)
            irq_peripherals.append(irq_peripheral)

        irq_peripherals.sort(key=lambda p: p.inst_name)
        return irq_peripherals

    def _get_alert_peripherals(self):
        alert_peripherals = []
        self.devices()
        for entry in self.top['module']:
            inst_name = entry['name']
            if inst_name not in self.top["alert_module"]:
                continue

            if not entry['generate_dif']:
                continue

            for item in self.top['module']:
                if item['name'] == inst_name:
                    name = item['type']

                    regions = self.device_regions[inst_name]
                    if "core" in regions:
                        if_name = "core"
                    elif "regs" in regions:
                        if_name = "regs"
                    elif "cfg" in regions:
                        if_name = "cfg"
                    else:
                        if_name = None
                    region = regions[if_name]
                    base_addr_name = region.base_addr_name().as_c_define()
                    break

            # If alerts are routed to the external interface, there is no need for DIFs, etc ...
            if 'outgoing_alert' in entry:
                continue

            dif_alert_name = self.device_alerts[inst_name][0]
            num_alerts = len(self.device_alerts[inst_name])

            top_alert_name = (self._top_name +
                              Name(["Alert", "Id"]) +
                              Name.from_snake_case(dif_alert_name))
            top_alert_name = top_alert_name.as_c_enum()

            # Get DIF compliant, instance-agnostic alert names.
            dif_alert_name = dif_alert_name.replace(inst_name, f"dif_{name}_alert", 1)
            dif_alert_name = Name.from_snake_case(dif_alert_name).as_c_enum()

            alert_peripheral = AlertTestPeripheral(name, inst_name, base_addr_name,
                                                   top_alert_name, dif_alert_name, num_alerts)
            alert_peripherals.append(alert_peripheral)

        alert_peripherals.sort(key=lambda p: p.inst_name)
        return alert_peripherals
