"""
Dell iDRAC Control v0.1
Maintained by Joel Cressy (joel@jtcressy.net)

Requirements:
    - Python >=3.6
    - Requires that ipmitool be installed on your system
    - Requires that ipmi over lan be enabled in the DRAC of your server

Features:
    - Set the user-defined LCD text of most Dell PowerEdge servers generation 9 and above
        - Maximum string length is 14 characters
    - Get the current LCD text at any time
    - Control power with `Host().power_[on, off, cycle, reset]()`
    - Get dictionary of chassis status with `Host().status()`
    - Get power state with `Host().powerstate`

Example usage:
```
    from drac_management import Host
    my_host = Host("ip address or dns name", "username", "password", lcdstring=["lcd text"], port=[623])
    # DO NOT set `lcdstring` if you do not intend to change the host's LCD string!
    print(my_host.lcdstring)
    #> lcd text
    my_host.lcdstring = "new text"
    print(my_host.lcdstring)
    #> new text
    print(my_host.powerstate)
    #> off
    my_host.power_on()
    print(my_host.powerstate)
    #> on
```
LCD text is automatically set whenever you update my_host.lcdstring
    or if you specify it when instantiating a copy of `Host`

"""
import subprocess
import getpass
import json

class Host:
    def __init__(self, host: str, user: str, password: str, lcdstring: str=None, port: int=623, metadata: dict = None):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.metadata = metadata
        self._name = lcdstring
        # self.ping()
        if lcdstring:
            self.lcdstring = lcdstring
        #     self._set_lcd_string(lcdstring)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value
        self.lcdstring = value

    @staticmethod
    def from_dict(input_dict: dict):
        return Host(
            input_dict['host'],
            input_dict['user'],
            input_dict['password'],
            input_dict.get('lcdstring', None),
            input_dict.get('port', 623),
            input_dict.get('metadata', None)
        )

    @staticmethod
    def from_instackenv_json(filename: str) -> list:
        output = []
        with open(filename, 'r') as fp:
            data = json.load(fp)
            for node in data['nodes']:
                omit = ['pm_addr', 'pm_user', 'pm_password', 'name']
                metadata = dict([(k, v) for k,v in node.items() if k not in omit])
                output.append(
                    Host.from_dict({
                        'host': node['pm_addr'],
                        'user': node['pm_user'],
                        'password': node['pm_password'],
                        'lcdstring': node['name'],
                        'metadata': metadata
                    })
                )
        return output

    def to_dict(self) -> dict:
        output = dict()
        output['host'] = self.host
        output['user'] = self.user
        output['password'] = self.password
        output['lcdstring'] = self.lcdstring
        output['port'] = self.port
        output['metadata'] = self.metadata
        return output

    @staticmethod
    def to_instackenv_json(hosts: list) -> str:
        outdict = {}
        nodelist = []
        for host in hosts:
            data = {}
            data['name'] = host.lcdstring
            data.update(host.metadata if host.metadata else {})
            data['pm_addr'] = host.host
            data['pm_user'] = host.user
            data['pm_password'] = host.password
            nodelist.append(data)
        outdict['nodes'] = nodelist
        return json.dumps(outdict)

    def _send_command(self, cmd: str) -> str:
        output = subprocess.getoutput(f"ipmitool -I lanplus -H {self.host} -U {self.user} -P {self.password} {cmd}")
        return output

    @property
    def lcdstring(self) -> str:
        if self.ping():
            output = self._send_command("delloem lcd info")
            try:
                lcdstring = output.split()[output.split().index("Text:")+1]
            except Exception as e:
                print(e, f"for host {self.host}", output)
                return None
            return lcdstring

    @lcdstring.setter
    def lcdstring(self, value: str):
        if type(value) is not str:
            raise TypeError(f"LCD string must be of type str, not {type(value)}")
        if len(value) > 14:
            raise ValueError("LCD String length cannot be more than 14 characters")
        output = self._set_lcd_string(value)

    def _set_lcd_string(self, value: str):
        if self.ping():
            return self._send_command(f"delloem lcd set mode userdefined '{value}'")

    def ping(self) -> bool:
        output = "Error" not in self.status().keys()
        return output

    def status(self) -> dict:
        """
        Get the current status of the machine
        :return: dict object containing statuses
        """
        result = dict()
        output = self._send_command("chassis status")
        lines = output.split('\n')
        for line in lines:
            try:
                k, v = line.split(':')
                result[k.strip()] = v.strip()
            except ValueError:
                try:
                    result['err'] = line
                except:
                    pass
        return result

    @property
    def powerstate(self) -> str:
        return self.status().get("System Power") if self.ping() else None

    def power_on(self) -> bool:
        """
        Power on the machine
        :return: bool: successful or not
        """
        return bool(self._send_command("chassis power on")) if self.ping() else False

    def power_off(self, soft: bool=True) -> bool:
        """
        Power off the machine gracefully or not gracefully with soft=False
        :param soft: bool: default True, Set to False to power off without OS shutdown (hard)
        :return:
        """
        return bool(self._send_command(f"chassis power {'soft' if soft else 'off'}")) if self.ping() else False

    def power_cycle(self) -> bool:
        """
        Perform a cold reset on the machine
        :return: bool: successful or not
        """
        return bool(self._send_command("chassis power cycle")) if self.ping() else False

    def power_reset(self) -> bool:
        """
        Perform a warm reset on the machine
        :return: bool: successful or not
        """
        return bool(self._send_command("chassis power reset")) if self.ping() else False


if __name__ == "__main__":
    print("drac_management testing")
    test_host = Host(
        input("iDRAC IP to test against: "),
        input("Username: "),
        getpass.getpass("Password: ")
    )
    if test_host.ping():
        print("Host status:\n", test_host.status())
        print("Current LCD string:", test_host.lcdstring)
        if input("Change LCD string? [y/N]: ").lower() == 'y':
            test_host.lcdstring = input("Input new LCD string (max 14 chars): ")[0:14]
            print("LCD string set to", test_host.lcdstring)
        else:
            print("LCD string unchanged")
        print("Power state:", test_host.powerstate)
        if input("Change power state? [y/N]: ").lower() == 'y':
            actions = {
                'on': test_host.power_on,
                'soft': test_host.power_off,
                'off': lambda: test_host.power_off(soft=False),
                'cycle': test_host.power_cycle,
                'reset': test_host.power_reset,
            }
            result = actions[input(f"Enter action ({'/'.join([x for x in actions.keys()])}): ")]()
            print(result)
            print("New power state:", test_host.powerstate)
    else:
        print("Failed to connect to", test_host.host, ": Either the host is down/unreachable or wrong username/password")
