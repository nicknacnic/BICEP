# BICEP 💪
BloxOne/UDDI Infoblox Cloud Expenditure Probe. A tool that identifies potential quality of life issues for Infoblox BloxOne/UDDI customers.
## BICEP


## Usage

### Installation:
Tap the formulae.
```git clone https://github.com/BICEP/```

Run the script.
```python bicep.py -s > output.txt```

> [!TIP]
> Use -s for summary, v for verbose.

### Overview:
This script is designed to help clean up your macOS system by uninstalling Homebrew packages and casks that haven't been used for a significant amount of time.

### How It Works:
This script analyzes DHCP data from CSV files to identify top clients, correlate leases to networks, and flag misbehaving clients. It:

1. Parses DHCP settings to get network and lease time info.
2. Reads syslog entries to gather lease data (MAC address, IPs, timestamps).
3. Identifies top clients by lease count.
4. Correlates leases to networks based on IP and CIDR.
5. Finds misbehaving clients requesting leases before their time is up.
6. Outputs summaries of top networks and misbehaving clients.
7. It helps track DHCP usage and detect issues with network clients.

### Notes:
> [!CAUTION]
> x2-xx-xx-xx-xx-xx, x6-xx-xx-xx-xx-xx, xA-xx-xx-xx-xx-xx, and xE-xx-xx-xx-xx-xx are Apple private MAC addresses. They may alter your counts if clients are leaving and re-joining networks regularly.

## To Do
- [ ] Integrate to Postman for CSP MAC Fingerprint data.
- [ ] Fix summary and verbose errors.
