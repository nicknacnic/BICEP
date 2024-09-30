import csv
import ipaddress
from collections import defaultdict
from collections import Counter
from datetime import datetime

# Step 1: Parse DHCP settings from CSV file
def parse_dhcp_csv(file_path):
    print("Parsing DHCP settings CSV...")
    networks = {}
    try:
        with open(file_path, mode='r') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                if row[0] == "ipamdhcp-v3-addressblock":
                    network_name = row[1]
                    network_address = row[4]
                    cidr_prefix = row[4] + "/16"  # Assuming CIDR /16 based on provided example
                    # Handle the possibility of an empty or invalid lease_time
                    try:
                        lease_time = int(row[10]) if row[10].isdigit() else 3600  # Default lease time = 3600s (1 hour)
                    except ValueError:
                        lease_time = 3600  # Default to 3600 seconds (1 hour)
                    networks[cidr_prefix] = {
                        'network': network_address,
                        'lease_time': lease_time  # Lease time in seconds
                    }
        print(f"Finished parsing DHCP CSV. Found {len(networks)} networks.")
    except Exception as e:
        print(f"Error parsing CSV: {e}")
    return networks

# Step 2: Parse syslog CSV entries (reversed order)
def parse_syslog(file_path):
    print("Parsing DHCP syslog CSV in reverse order...")
    dhcp_leases = []
    try:
        with open(file_path, mode='r') as file:
            csv_reader = list(csv.reader(file))  # Read the entire CSV into a list
            csv_reader.reverse()  # Reverse the order of the rows to process from the oldest to the most recent
            for row in csv_reader:
                # Skip invalid rows or headers
                try:
                    ipaddress.ip_address(row[4])  # Try parsing the IP to check its validity
                except ValueError:
                    continue  # Skip rows with invalid IP addresses

                # Extracting fields from the CSV
                timestamp = row[0]
                mac_address = row[2]
                leased_ip = row[4]
                server_ip = row[6]

                # Store the parsed data
                dhcp_leases.append({
                    'timestamp': timestamp,
                    'mac_address': mac_address,
                    'leased_ip': leased_ip,
                    'server_ip': server_ip
                })
        print(f"Finished parsing syslog CSV. Found {len(dhcp_leases)} leases.")
    except Exception as e:
        print(f"Error parsing syslog CSV: {e}")
    return dhcp_leases

# Step 3: Get the top clients by number of leases
def get_top_clients(dhcp_leases, top_n=25):
    print("Analyzing top DHCP clients...")
    mac_address_counter = Counter([lease['mac_address'] for lease in dhcp_leases])
    top_clients = mac_address_counter.most_common(top_n)
    print(f"\n--- Top {top_n} DHCP Clients ---")
    for client, lease_count in top_clients:
        print(f"Client: {client}, Leases: {lease_count}")
    return top_clients

# Step 4: Correlate DHCP leases to networks using full CIDR
def correlate_leases_to_networks(dhcp_leases, networks):
    print("Correlating DHCP leases to networks...")
    correlated_data = defaultdict(list)
    network_lease_count = Counter()

    for lease in dhcp_leases:
        try:
            leased_ip = ipaddress.ip_address(lease['leased_ip'])
        except ValueError:
            continue  # Skip invalid IP addresses

        for cidr_prefix, network_info in networks.items():
            if leased_ip in ipaddress.ip_network(cidr_prefix):
                correlated_data[network_info['network']].append(lease)  # Store just the network prefix
                network_lease_count[network_info['network']] += 1
                break

    print(f"Finished correlating {len(dhcp_leases)} leases to networks.")
    print()
    return correlated_data, network_lease_count

# Step 5: Identify misbehaving clients
def find_misbehaving_clients(dhcp_leases, networks):
    print("Identifying misbehaving clients...")
    client_last_seen = defaultdict(lambda: None)  # To track last lease request time for each client
    misbehaving_clients = defaultdict(lambda: defaultdict(int))  # Track misbehaviors per network per client

    for lease in dhcp_leases:
        try:
            leased_ip = ipaddress.ip_address(lease['leased_ip'])
        except ValueError:
            continue  # Skip invalid IP addresses

        # Match the leased IP with the appropriate network
        for cidr_prefix, network_info in networks.items():
            if leased_ip in ipaddress.ip_network(cidr_prefix):
                lease_time = network_info['lease_time']
                network_prefix = network_info['network']  # Use only the network prefix (e.g., 10.10.0.0/16)
                break
        else:
            continue  # Skip if no network match

        client = lease['mac_address']
        current_time = datetime.strptime(lease['timestamp'], '%Y-%m-%dT%H:%M:%S.%f')

        # Check if client has a previous lease time
        if client_last_seen[client]:
            last_time = client_last_seen[client]
            time_difference = (current_time - last_time).total_seconds()

            if time_difference < 0:
                print(f"Skipping out-of-order lease for {client}: Last lease {last_time}, Current lease {current_time}")
                continue

            # Only record misbehaving clients if they request a lease before their full lease time is up
            if time_difference < lease_time:
                # Increment the misbehavior count for this client and network
                misbehaving_clients[client][network_prefix] += 1

        # Update the last seen time for the client
        client_last_seen[client] = current_time

    print(f"Found {len(misbehaving_clients)} misbehaving clients.")
    return misbehaving_clients

# Step 6: Convert seconds to hours and minutes
def format_time(seconds):
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"

# Step 7: Output misbehaving clients (summarized and ordered)
def output_misbehaving_clients_summary(misbehaving_clients):
    misbehaving_summary = []
    
    for client, networks in misbehaving_clients.items():
        for network, count in networks.items():
            misbehaving_summary.append((client, network, count))
    
    # Sort by the count (most to least misbehaviors)
    misbehaving_summary = sorted(misbehaving_summary, key=lambda x: x[2], reverse=True)
    
    # Output the summary
    for client, network, count in misbehaving_summary:
        print(f"Client: {client} misbehaved {count} times on Network: {network}")

# Step 8: Output top networks by client lease count
def output_top_networks(network_lease_count, top_n=10):
    print(f"\n--- Top {top_n} Networks by Lease Count ---")
    top_networks = network_lease_count.most_common(top_n)
    for network, lease_count in top_networks:
        print(f"Network: {network}, Leases: {lease_count}")

# Step 9: Output top networks by lease count
def output_top_networks(network_lease_count, top_n=25):
    print(f"\n--- Top {top_n} Networks by Lease Count ---")
    top_networks = network_lease_count.most_common(top_n)
    for network, lease_count in top_networks:
        print(f"Network: {network}, Leases: {lease_count}")

# Main function to parse, analyze, and output results
def main():
    dhcp_settings_file = 'dhcp_settings.csv'  # Replace with your actual CSV file path
    syslog_file = 'dhcp_syslog.csv'  # Replace with your actual syslog CSV file path

    # Step 1: Parse the DHCP settings CSV
    networks = parse_dhcp_csv(dhcp_settings_file)
    
    # Step 2: Parse the syslog CSV file in reverse order
    dhcp_leases = parse_syslog(syslog_file)

    # Step 3: Get the top clients by number of leases
    top_clients = get_top_clients(dhcp_leases)

    # Step 4: Output the top networks by lease count
    correlated_data, network_lease_count = correlate_leases_to_networks(dhcp_leases, networks)
    
    # Step 5: Output the top networks by lease count (use the correct 'network_lease_count')
    output_top_networks(network_lease_count, top_n=25)
    
    # Step 6: Identify misbehaving clients
    misbehaving_clients = find_misbehaving_clients(dhcp_leases, networks)

    # Step 7: Output the summarized and ordered misbehaving clients
    output_misbehaving_clients_summary(misbehaving_clients)

if __name__ == "__main__":
    main()
