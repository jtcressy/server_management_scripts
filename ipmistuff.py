#! /usr/bin/env python3
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
    parser.add_argument("--nodes", nargs='+', help="space-separated list of machine names to perform action")
    parser.add_argument("--all", action="store_true", help="Select all machines to perform action")
    parser.add_argument("--identify-on", action="store_true", help="Enable identity light on selected machines")
    parser.add_argument("--identify-off", action="store_true", help="Disable identity light on selected machines")
    args = parser.parse_args()
    try:
        hostconfigs = Host.from_instackenv_json(args.instackenv)
        selected_nodes = args.nodes
        for host in hostconfigs:
            lcdstring = host.name
            if args.all or lcdstring in selected_nodes:
                if args.identify_on:
                    host.identify()
                    print(lcdstring, "ID LED enabled")
                elif args.identify_off:
                    host.identify(False)
                    print(lcdstring, "ID LED disabled")
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
        # lets avoid printing the pm_password by cutting it out of the dictionary
        nodes = [dict([(k,v) for k, v in node.items() if k not in ['pm_password']]) for node in nodes]
        header = nodes[0].keys()
        rows = [x.values() for x in nodes]
        print(tabulate.tabulate(rows, header))
    except KeyboardInterrupt:
        sys.exit(0)
