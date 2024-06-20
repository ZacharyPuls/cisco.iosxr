#
# -*- coding: utf-8 -*-
# Copyright 2024 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import absolute_import, division, print_function


__metaclass__ = type

"""
The iosxr_vrf_address_family config file.
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to its desired end-state is
created.
"""
import q

from ansible.module_utils.six import iteritems
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.rm_base.resource_module import (
    ResourceModule,
)
from ansible_collections.ansible.netcommon.plugins.module_utils.network.common.utils import (
    dict_merge,
)

from ansible_collections.cisco.iosxr.plugins.module_utils.network.iosxr.facts.facts import Facts
from ansible_collections.cisco.iosxr.plugins.module_utils.network.iosxr.rm_templates.vrf_address_family import (
    Vrf_address_familyTemplate,
)


class Vrf_address_family(ResourceModule):
    """
    The iosxr_vrf_address_family config class
    """

    def __init__(self, module):
        super(Vrf_address_family, self).__init__(
            empty_fact_val={},
            facts_module=Facts(module),
            module=module,
            resource="vrf_address_family",
            tmplt=Vrf_address_familyTemplate(),
        )
        self.parsers = [
            "address_family",
            "export.route_policy",
            "export.route_target",
            "export.to.default_vrf.route_policy",
            "export.to.vrf.allow_imported_vpn",
            "import_config.route_target",
            "import_config.route_policy",
            "import_config.from_config.bridge_domain.advertise_as_vpn",
            "import_config.from_config.default_vrf.route_policy",
            "import_config.from_config.vrf.advertise_as_vpn",
            "maximum.prefix",
        ]

    def execute_module(self):
        """Execute the module

        :rtype: A dictionary
        :returns: The result from module execution
        """
        if self.state not in ["parsed", "gathered"]:
            self.generate_commands()
            self.run_commands()
        return self.result

    def generate_commands(self):
        """Generate configuration commands to send based on
        want, have and desired state.
        """
        wantd = self.want
        haved = self.have

        wantd = self._vrf_list_to_dict(wantd)
        haved = self._vrf_list_to_dict(haved)

        # if state is merged, merge want onto have and then compare
        if self.state == "merged":
            wantd = dict_merge(haved, wantd)

        # if state is deleted, empty out wantd and set haved to wantd
        if self.state == "deleted":
            haved = {k: v for k, v in iteritems(haved) if k in wantd or not wantd}
            wantd = {}

        if self.state in ["overridden", "deleted"]:
            for k, have in haved.items():
                if k not in wantd:
                    self._compare(want={}, have=have)

        self._compare(want=wantd, have=haved)

    def _compare(self, want, have):
        """Custom handling of afs option
        :params want: the want VRF dictionary
        :params have: the have VRF dictionary
        """
        wafs = want.get("address_families", {})
        hafs = have.get("address_families", {})
        for name, entry in iteritems(wafs):
            begin = len(self.commands)
            af_have = hafs.pop(name, {})

            self.compare(parsers=self.parsers, want=entry, have=af_have)
            if len(self.commands) != begin:
                self.commands.insert(
                    begin,
                    self._tmplt.render(
                        {
                            "afi": entry.get("afi"),
                            "safi": entry.get("safi"),
                        },
                        "address_families",
                        False,
                    ),
                )

        # for deleted and overridden state
        if self.state in ["overridden", "deleted"]:
            begin = len(self.commands)
            for name, entry in iteritems(hafs):
                for af_key, af in entry.get("address_families", {}).items():
                    self.addcmd(
                        {
                            "afi": af.get("afi"),
                            "safi": af.get("safi"),
                        },
                        "address_family",
                        True,
                    )
                    if len(self.commands) != begin:
                        self.commands.insert(begin, self._tmplt.render({"name": name}, "name", False))

    def _vrf_list_to_dict(self, entry):
        """Convert list of items to dict of items
           for efficient diff calculation.
        :params entry: data dictionary
        """

        for vrf in entry:
            if "address_families" in vrf:
                vrf["address_families"] = {
                    (x["afi"], x.get("safi")): x for x in vrf["address_families"]
                }
        # q(entry)
        entry = {x["name"]: x for x in entry}
        # q(entry)
        return entry
