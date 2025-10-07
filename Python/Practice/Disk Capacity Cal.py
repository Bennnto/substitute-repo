print("======== Dishonest Capacity Disk Calculator ========")
print("Please Enter Your Disk Capacity unit in GB or TB unit")
unit = input(">")
#Calculate the amount that 
if unit == 'tb' or unit == 'TB':
    discrepancy = 1000000000000 / 1099511627776
if unit == 'gb' or unit == 'GB':
    discrepancy = 1000000000 / 1073741824

#Ask for disk advertising capacity
print("Please Enter Your Advertising Disk Capacity with out unit")
advertising_Capa = input(">")
advertising_Capa = float(advertising_Capa)

#Real Capacity
real_Capa = str(round(advertising_Capa * discrepancy, 2))

print("The actual Capacity of your disk is", real_Capa)