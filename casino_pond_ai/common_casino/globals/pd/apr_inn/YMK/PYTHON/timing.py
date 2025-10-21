#! /usr/local/bin/python3.12 -u
import os
import re
import subprocess
import time
import gzip
import glob
import pandas as pd



# Define column names
columns = [
    "WNS(setup)", "TNS(setup)", "Count(setup)",
    "WNS(hold)", "TNS(hold)", "Count(hold)",
    "Power", "EU", "TU", "Congestion", "Short",
    "SLVT", "LVT", "RVT", "HVT", "Total Inst", "Run time"
]

# Define row names
rows = ["init", "place", "cts", "postcts", "route", "postroute", "chipfinish"]

# Create an empty DataFrame
data = pd.DataFrame(index=rows, columns=columns)

# Base directory for files
base_dir = "./report"

# Function to extract data from files
def extract_data_from_file(file_path, is_hold=False):
    with gzip.open(file_path, 'rt') as f:
        lines = f.readlines()

    # Initialize extracted data
    extracted_data = {
        "WNS(setup)" if not is_hold else "WNS(hold)": None,
        "TNS(setup)" if not is_hold else "TNS(hold)": None,
        "Count(setup)" if not is_hold else "Count(hold)": None,
    }

    # Extract required data from the file
    reg2reg_section = False
    for line in lines:
        if "reg2reg" in line:  # Start of reg2reg section
            reg2reg_section = True
        elif reg2reg_section and "WNS (ns):" in line:
            values = re.findall(r"[-+]?\d*\.\d+|\d+", line)
            extracted_data["WNS(setup)" if not is_hold else "WNS(hold)"] = values[1] if len(values) > 1 else None
        elif reg2reg_section and "TNS (ns):" in line:
            values = re.findall(r"[-+]?\d*\.\d+|\d+", line)
            extracted_data["TNS(setup)" if not is_hold else "TNS(hold)"] = values[1] if len(values) > 1 else None
        elif reg2reg_section and "Violating Paths:" in line:
            values = re.findall(r"\d+", line)
            extracted_data["Count(setup)" if not is_hold else "Count(hold)"] = values[1] if len(values) > 1 else None
        elif reg2reg_section and "All Paths:" in line:
            reg2reg_section = False  # End of reg2reg section
    return extracted_data

# Search for files and extract data
for row in rows:
    # Search for setup files
    setup_pattern = os.path.join(base_dir, row, "*sum*gz")
    setup_files = glob.glob(setup_pattern)
    if setup_files:
        extracted_setup = extract_data_from_file(setup_files[0], is_hold=False)
        data.loc[row, "WNS(setup)"] = extracted_setup["WNS(setup)"]
        data.loc[row, "TNS(setup)"] = extracted_setup["TNS(setup)"]
        data.loc[row, "Count(setup)"] = extracted_setup["Count(setup)"]

    # Search for hold files
    hold_pattern = os.path.join(base_dir, row, "*hold*sum*gz")
    hold_files = glob.glob(hold_pattern)
    if hold_files:
        extracted_hold = extract_data_from_file(hold_files[0], is_hold=True)
        data.loc[row, "WNS(hold)"] = extracted_hold["WNS(hold)"]
        data.loc[row, "TNS(hold)"] = extracted_hold["TNS(hold)"]
        data.loc[row, "Count(hold)"] = extracted_hold["Count(hold)"]


#Overflow 
for row in rows:
    # Search for setup files (where Routing Overflow is present)
    setup_pattern = os.path.join(base_dir, row, "*sum*gz")
    setup_files = glob.glob(setup_pattern)
    if setup_files:
        # Extract Routing Overflow value
        with gzip.open(setup_files[0], 'rt') as f:
            lines = f.readlines()
        
        for line in lines:
            if "Routing Overflow" in line:  # Check for the Routing Overflow line
                # Extract horizontal (H) and vertical (V) overflow percentages
                match = re.findall(r"[-+]?\d*\.\d+%", line)  # Extract percentages
                if len(match) == 2:  # Ensure both H and V values are present
                    congestion_value = f"{match[0]}/{match[1]}"  # Format as H/V
                    data.loc[row, "Congestion"] = congestion_value  # Save formatted value
                break  # Stop after finding the relevant line



#Total Power

for row in rows:
    # Search for power report files
    power_pattern = os.path.join(base_dir, row, "*.power")
    power_files = glob.glob(power_pattern)
    if power_files:
        # Extract Total Power value
        with open(power_files[0], 'r') as f:
            lines = f.readlines()
        
        for line in lines:
            if "Total Power:" in line:  # Check for the Total Power line
                match = re.findall(r"[-+]?\d*\.\d+|\d+", line)  # Extract numeric value
                if match:
                    data.loc[row, "Power"] = match[0]  # Save Total Power value
                break  # Stop after finding the relevant line


#EU TU



for row in rows:
    # Search for EU_TU files
    eu_tu_pattern = os.path.join(base_dir, row, "*EU_TU")
    eu_tu_files = glob.glob(eu_tu_pattern)
    if eu_tu_files:
        # Extract EU and TU values
        with open(eu_tu_files[0], 'r') as f:
            lines = f.readlines()

        eu_value, tu_value = None, None
        for line in lines:
            # Extract % Pure Gate Density #5 for EU
            if "% Pure Gate Density #5" in line and "Subtracting MACROS and BLOCKAGES" in line:
                match = re.findall(r"[-+]?\d*\.\d+%", line)  # Extract percentages
                if match:
                    eu_value = match[0]  # First matched percentage

            # Extract % Core Density (Counting Std Cells and MACROs) for TU
            elif "% Core Density (Counting Std Cells and MACROs)" in line:
                match = re.findall(r"[-+]?\d*\.\d+%", line)  # Extract percentages
                if match:
                    tu_value = match[0]  # First matched percentage

            # Break if both values are found
            if eu_value and tu_value:
                break

        # Save the extracted values to the DataFrame
        data.loc[row, "EU"] = eu_value
        data.loc[row, "TU"] = tu_value


#Vth

for row in rows:
    # Search for Vth.rpt files
    vth_pattern = os.path.join(base_dir, row, "*Vth.rpt")
    vth_files = glob.glob(vth_pattern)
    if vth_files:
        # Extract SLVT, LVT, RVT, HVT, and Total Inst values
        with open(vth_files[0], 'r') as f:
            lines = f.readlines()
        
        slvt, lvt, rvt, hvt, total_inst = None, None, None, None, None
        for line in lines:
            # Extract SLVT Ratio
            if "SLVT" in line:
                match = re.findall(r"\d+\.\d+%", line)  # Extract percentage value
                if match:
                    slvt = match[0]  # First matched percentage for SLVT
            # Extract LVT Ratio
            elif "LVT" in line:
                match = re.findall(r"\d+\.\d+%", line)
                if match:
                    lvt = match[0]  # First matched percentage for LVT
            # Extract RVT Ratio
            elif "RVT" in line:
                match = re.findall(r"\d+\.\d+%", line)
                if match:
                    rvt = match[0]  # First matched percentage for RVT
            # Extract HVT Ratio
            elif "HVT" in line:
                match = re.findall(r"\d+\.\d+%", line)
                if match:
                    hvt = match[0]  # First matched percentage for HVT
            # Extract Total Instance Count
            elif "Total Instance Count" in line:
                match = re.findall(r"\d+", line)  # Extract numeric value
                if match:
                    total_inst = match[0]  # Total Instance Count

        # Save the extracted values to the DataFrame
        data.loc[row, "SLVT"] = slvt
        data.loc[row, "LVT"] = lvt
        data.loc[row, "RVT"] = rvt
        data.loc[row, "HVT"] = hvt
        data.loc[row, "Total Inst"] = total_inst

#Short


for row in rows:
    # Search for Short.rpt files
    short_pattern = os.path.join(base_dir, row, "Short.rpt")
    short_files = glob.glob(short_pattern)
    if short_files:
        # Extract Short value
        with open(short_files[0], 'r') as f:
            lines = f.readlines()
        
        short_value = None
        for line in lines:
            if "Short" in line:  # Look for the line containing the "Short" keyword
                match = re.findall(r"\d+", line)  # Extract numeric value
                if match:
                    short_value = match[0]  # Get the first matched number
                break  # Stop after finding the relevant line

        # Save the extracted Short value to the DataFrame
        data.loc[row, "Short"] = short_value



# Save the data to a CSV file
data.to_csv("table_with_setup_and_hold.csv", index=True)
