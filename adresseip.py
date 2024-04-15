#import ipaddress

#ip_address = input("Enter IP address: ")
#subnet_mask = input("Enter subnet mask: ")

#network = ipaddress.IPv4Network(f"{ip_address}/{subnet_mask}", strict=False)

#print(f"Network Address: {network.network_address}")
#print(f"Broadcast Address: {network.broadcast_address}")
#print(f"Number of Hosts: {network.num_addresses}")
#print(f"Number of Users: {network.num_addresses - 2}")  # Subtracting network and broadcast addresses

# Calculate network address manually
#ip_address = input("Enter IP address: ")
#subnet_mask = input("Enter subnet mask: ")

#ip_parts = ip_address.split('.')
#subnet_parts = subnet_mask.split('.')

#network_address = []
#for i in range(4):
#    network_address.append(str(int(ip_parts[i]) & int(subnet_parts[i])))
#network_address = '.'.join(network_address)
#print(f"Network Address (Manual): {network_address}")

# Calculate broadcast address manually
#subnet_bits = sum([bin(int(x)).count('1') for x in subnet_parts])
#host_bits = 32 - subnet_bits
#broadcast_address = '.'.join([
#  str(
#      (
#          (int(network_address.split('.')[i]) | (2**host_bits - 1)) >> (24 - 8 * i)
#      ) & 255
# )
#    for i in range(4)
#])
#print(f"Broadcast Address (Manual): {broadcast_address}")

# Calculate number of hosts
#num_addresses = 2**(host_bits)
#num_hosts = num_addresses - 2
#print(f"Number of Hosts (Manual): {num_hosts}")


#
address = [192,168,9,152] #inserer adresse ip
masque = [255,255,0,128] #inserer masque ip
dict_masque = {255:8,254:7,252:6,248:5,240:4,224:3,192:2,128:1,0:0} # dictionnaire qui traduit la valeur décimal en nombre de bit 
dict_2masq ={(256-2**i):(8-i) for i in range(9)}
masq_déc = 0 # déclaration de la variable masq_déc pour compter le nbr d'hôtes disponible
address_reso = [] # déclaration de la liste address_reso 
address_diff = [] # déclaration de la liste address_diff
nb_hotes = [] # déclaration de la liste nb_hotes

for i in range(4): # Pour i dans un pas de 4        0 1 2 3
    address_reso.append(masque[i] & address[i]) #ajoute pour chaque itération de i le masque et l'address avec un & logique pour chaque octets à la liste address_reso 
    address_diff.append(address_reso[i] + 255 - masque[i]) #ajoute pour chaque iteration de i à l'address_reso le complément à 255 du masque puis stocke la liste dans address_diff 
    masq_déc=masq_déc+dict_2masq[masque[i]] # pour chaque itération de i créé une somme de masq_déc et de la valeur binaire de 

num_addresses = 2**(32 - masq_déc)-2


print("l'addresse réseaux est :", address_reso)
print("l'adresse de diffusion :", address_diff)
print("le nombre d'hotes possibles est de :", num_addresses)
print(dict_2masq)

resume_dict = {str(i): f"{i:04b}" for i in range(16)}