import gseapy

print("Loading LINCS_L1000_Chem_Pert_up...")
lib_up = gseapy.get_library(name="LINCS_L1000_Chem_Pert_up")
print(f"Loaded {len(lib_up)} gene sets from LINCS up")

lib_down = gseapy.get_library(name="LINCS_L1000_Chem_Pert_down")
print(f"Loaded {len(lib_down)} gene sets from LINCS down")

# Search for metformin and imatinib in terms
met_up = [k for k in lib_up.keys() if "metformin" in k.lower()]
met_down = [k for k in lib_down.keys() if "metformin" in k.lower()]
print(f"Metformin terms: up={len(met_up)}, down={len(met_down)}")
if met_up:
    print("  Sample Metformin up term:", met_up[0], "gene count:", len(lib_up[met_up[0]]))

ima_up = [k for k in lib_up.keys() if "imatinib" in k.lower()]
ima_down = [k for k in lib_down.keys() if "imatinib" in k.lower()]
print(f"Imatinib terms: up={len(ima_up)}, down={len(ima_down)}")
if ima_up:
    print("  Sample Imatinib up term:", ima_up[0], "gene count:", len(lib_up[ima_up[0]]))
