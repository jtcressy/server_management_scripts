#! /usr/bin/env python
from drac_management import Host
import sys
import tabulate
import json
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage the iDRAC interfaces of multiple servers")
    parser.add_argument("instackenv", help="Formatted json file containing ipmi connection details of multiple servers")
    parser.add_argument("--all-power-on", action="store_true", help="Power on all machines")
    parser.add_argument("--all-power-off", action="store_true", help="Gracefully shutdown all machines")
    parser.add_argument("--all-power-cycle", action="store_true", help="Cold-reboot all machines (non-graceful)")
    parser.add_argument("--all-power-reset", action="store_true", help="Warm-reboot all machines (non-graceful)")
    parser.add_argument("--force", action="store_true", help="If applicable, non-gracefully perform the action (e.g. force power off)")
    args = parser.parse_args()
    try:
        hostconfigs = Host.from_instackenv_json(args.instackenv)
        for host in hostconfigs:
            if args.all_power_off:
                host.power_off(not args.force)
            elif args.all_power_on:
                host.power_on()
            elif args.all_power_cycle:
                host.power_cycle()
            elif args.all_power_reset:
                host.power_reset()
            else:
                "No action."
            print(host.lcdstring, "power state:", host.powerstate)
        nodes = json.loads(Host.to_instackenv_json(hostconfigs))['nodes']
        header = nodes[0].keys()
        rows = [x.values() for x in nodes]
        print(tabulate.tabulate(rows, header))
    except KeyboardInterrupt:
        sys.exit(0)
