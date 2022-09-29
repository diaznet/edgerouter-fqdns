# EdgeRouter FQDNs
FQDN script for Ubiquiti EdgeRouter.

# Purpose

The EdgeRouters are inexpensive, high-performamce prosumer routers with a lot of built-in functionalities.

I found however over the course of years that it was missing the possibility to create firewall rules based on hostnames and not only on IP addresses.

In a dynamic environment where IP addresses may change often, it could be necessary to build some firewall rules using the hosts' hostnames.

# Features

 - Adds possibility to create Firewall Address Groups that will be populated from a predefined FQDN.
 - Uses the Description field of Firewall Address Group objects in EdgeOS.
 - Adds/remove/Updates IP addresses at every run

# Caveats

- It is of upmost importance to have a reliable and stable Name Resolution in your environment. Firewall rules created for this script will rely on DNS and faulty Name Resolution might have unwanted consequences. Remember that relying on FQDN to create firewall rules might also not be a good idea in several use cases.
- Firewall Address Groups names in EdgeRouter OS are limited to 28 charasters maximum. Names will appear truncated, but it will not impact the script's functionalities as it uses the Description field.
- Currently it is not possible to launch Python scripts from EdgeRouter OS scheduler. Therefore the script is mainly a Python script embedded into a Bash script.
- It is a scheduled script run, therefore all DNS records might not be up tp date before the next run of the script. I however found that it was in general working well with a scheduled interval of 15 minutes.
- At every run it will commit then save new configuration lines. The UI and the console will not be available at this moment (commit lock).

# Installation

- Download latest copy of the script file wrapper_fqdns.sh
- Upload the script into EdgeRouter: /config/user-data/scripts/
   - Note: this folder is designed to hold users' scripts and does not get wiped during upgrades.
   - Note: you might need to chmod +x the script file after upload  
- Choose a desired interval and enable the script to run. Example with 15 minutes interval:

		set system task-scheduler task update_fqdns executable path /config/user-data/scripts/wrapper_fqdns.sh
		set system task-scheduler task update_fqdns interval 15m

Nopte that you can run the script manually to check if all is in order:

		ubnt@my_edgerouter:~$ sudo /config/user-data/scripts/wrapper_fqdns.sh
		ubnt@my_edgerouter:~$

# Usage

You can add new Firewall Address Group objects in the GUI or in the CLI.
Simply make sure that all objects have a description with the following string:

    FQDN-<fully.qualified.domain.name>

For example if we want to create a dynamic object that will resolve ftp.ch.debian.org for you, enter the following line in the CLI:

    set firewall group address-group Debian_CH_Update_Servers description FQDN-ftp.ch.debian.org

After manual run or at the next scheduled run of the script, the Firewall Address Group object will be populated with the IP address(es) resolved from the prefixed string in Description field.  
Example after 1st run of the script:

    ubnt@my_edgerouter:~$ show configuration commands | grep Debian
    set firewall group address-group Debian_CH_Update_Servers address 129.132.53.171
    set firewall group address-group Debian_CH_Update_Servers description FQDN-ftp.ch.debian.org
    ubnt@my_edgerouter:~$ 


This object will then be available for you to create a new firewall rule in EdgeRouter OS.
Example below creates a new Firewall rule 42 in Ruleset "Servers_Lan_In"


    set firewall name Servers_Lan_In rule 42 action accept
    set firewall name Servers_Lan_In rule 42 description 'Debian CH Update Servers'
    set firewall name Servers_Lan_In rule 42 destination group address-group Debian_CH_Update_Servers
    set firewall name Servers_Lan_In rule 42 destination port 443
    set firewall name Servers_Lan_In rule 42 log enable
    set firewall name Servers_Lan_In rule 42 protocol tcp
    set firewall name Servers_Lan_In rule 42 source group address-group My_Debian_Server
    
Check the [EdgeOS User Guide](https://dl.ubnt.com/guides/edgemax/EdgeOS_UG.pdf) for more information about Firewall Rules in EdgeRouters.

# Disclaimer

This script comes without warranty.
It may or may not harm your router.
Please use with care.
Any damage cannot be related back to the author.
The script has been tested and ran on my home environment for months.

# Compatibility

This script is currently working with latest EdgeRouter OS v2.0.9-hotfix.2  
The Python part of the script is compatible with Python 2.7. The embedded version of Python in EdgeOS is 2.7.13 at the time of writing this README.

# Todo's

- IPv6 support
- Custom prefix support (the Python script does, the Bash wrapper doesn't).

# Credits
Author: Jeremy Diaz
I used various posts on UI Community forums to create this script.
