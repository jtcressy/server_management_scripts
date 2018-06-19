#! /usr/bin/env python
from drac_management import Host
import sys
import tabulate
import json
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manage the iDRAC interfaces of multiple servers")
    parser.add_argument("instackenv", help="Formatted json file containing ipmi connection details of multiple servers")
    parser.add_argument("--power-on", action="store_true", help="Power on selected machines")
    parser.add_argument("--power-off", action="store_true", help="Gracefully shutdown selected machines")
    parser.add_argument("--power-cycle", action="store_true", help="Cold-reboot selected machines (non-graceful)")
    parser.add_argument("--power-reset", action="store_true", help="Warm-reboot selected machines (non-graceful)")
    parser.add_argument("--force", action="store_true", help="If applicable, non-gracefully perform the action (e.g. force power off)")
    parser.add_argument("--nodes", nargs='+', help="space-separated list of node names to perform action")
    parser.add_argument("--all", help="Select all nodes to perform action")
    args = parser.parse_args()
    try:
        hostconfigs = Host.from_instackenv_json(args.instackenv)
        selected_nodes = args.nodes
        for host in hostconfigs:
            lcdstring = host.name
            if lcdstring in selected_nodes or args.all:
                if args.power_on:
                    host.power_on()
                    print(lcdstring, "powered on")
                elif args.power_off:
                    host.power_off(not args.force)
                    print(lcdstring, "powered off")
                elif args.power_cycle:
                    host.power_cycle()
                    print(lcdstring, "power cycled")
                elif args.power_reset:
                    host.power_reset()
                    print(lcdstring, "power reset")
                print(lcdstring, "power state:", host.powerstate)
        nodes = json.loads(Host.to_instackenv_json(hostconfigs))['nodes']
        header = nodes[0].keys()
        rows = [x.values() for x in nodes]
        print(tabulate.tabulate(rows, header))
    except KeyboardInterrupt:
        sys.exit(0)
