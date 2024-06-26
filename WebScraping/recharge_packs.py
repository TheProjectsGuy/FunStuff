# Scrap plans for pre-paid recharge from websites
"""
    Because I'm too lazy to go through all plans. Just scrap them 
    using selenium, save them to an ODS spreadsheet, and analyze.
    Give me the cheapest plans (based on daily cost) with daily and
    fixed data renewals.
    
    Warning: Use at your own risk. Always confirm details from the
        official websites.
    
    Notes:
    1. Create the symlink to `selenium-manager` in the `envs` folder.
        See the path in the error message. This is if you're getting
        the error in the first run (after setup).
    2. I don't need "International Roaming" (for use only in India). 
        It also doesn't conform to the same design.
    3. Don't need "Talktime" (who uses it anyways? I hate calls). It 
        also breaks the validity side of scraping.
    
    Some additional notes about entries
    1. Value of "-1" in "Validity (Days)" means 'existing' (don't take
        such packs as they're add-ons)
    2. Value of "-1" in "Data Size (GB)" means 'unlimited' data
    3. Value of "Daily" for "Data Renewal" means the data quota renews
        every day (good for emergency, but usually more expensive).
        Value of "Data" means the data quota renews at the end of the
        validity period (fixed quota, don't cross it).
    4. The first sheet of the ODS file has to have the most plans.
    
    Notes for future improvements:
    - Maybe add functions for Jio as well
        - https://www.jio.com/selfcare/plans/mobility/jiophone-plans/
"""

# %%
import os
import sys
import pdb
import tyro
import time
import logging
import traceback
import pandas as pd
from typing import Literal
from selenium import webdriver
from dataclasses import dataclass, field
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.common.exceptions import \
        ElementClickInterceptedException


# %%
# Didn't need this code generated by Bard really (LOL)
import re
def find_non_integer_or_period(text):
    """
        Finds the index of the first non-integer or period character 
        using regex.
    """
    match = re.search(r"[^\d\.]", text)  # Match any non-digit char
    return match.start() if match else -1


# %%
sheet_columns = ["Cost (INR)", "Validity (Days)", "Data Size (GB)", 
                    "Data Renewal"]


# %%
@dataclass
class LocalArgs:
    # Network provider
    net_provider: Literal["airtel", "jio", "vi"] = "airtel"
    # Sheet number to analyze (see the ODS file for all packs)
    sheet_num: int = -1


# %%
web_addrs = {
    "airtel": "https://www.airtel.in/recharge-online",
    "vi": "https://www.myvi.in/prepaid/online-mobile-recharge",
}


# %%
# Get airtel prepaid data
def grab_airtel(driver):
    elems = driver.find_elements(By.CLASS_NAME, "tabs-single-content")
    dfs = { # The names of the plans (spreadsheet) and their content
        "names": [],
        "pd": [],
    }
    for elem in elems:
        # Each is a separate tab
        sheet_name = elem.get_attribute("data-tab-name")
        if sheet_name in ["International Roaming", 
                    "Inflight Roaming packs"] or \
                sheet_name.startswith("Talktime"):
            continue
        df = pd.DataFrame(columns=sheet_columns)
        # Get all plans
        packs = elem.find_elements(By.CLASS_NAME, 
                                    "pack-card-left-section")
        for i, pack in enumerate(packs):
            # Each is a plan
            details = pack.find_elements(By.CLASS_NAME, 
                                        "pack-card-detail")
            # Cost of plan
            cost = details[0].find_element(By.CLASS_NAME, # In INR
                                        "pack-card-heading").text[1:]
            df.at[i, df.columns[0]] = int(cost)
            # Validity (duration) of plan
            validity_segment = details[2].text.split("\n")
            assert validity_segment[1].lower() == "validity"
            validity = validity_segment[0].lower().split()  # Heading
            if len(validity) == 1:
                validity = validity[0]
                assert validity == "existing"
                validity = -1   # Existing validity (over a pack)
            elif validity[1].startswith("day"):
                validity = int(validity[0])
            elif validity[1].startswith("month"):
                # 1 month = 28 days (Airtel T&C; for some reason)
                validity = int(validity[0]) * 28
            else:
                raise ValueError(f"Unknown validity: {validity}")
            df.at[i, df.columns[1]] = validity
            # Amount of data and renewal (validity) of data in plan
            data_size = details[1].find_element(By.CLASS_NAME, 
                                        "pack-card-heading").text
            data_renewal = details[1].find_element(By.CLASS_NAME, 
                                    "pack-card-sub-heading").text
            if data_size[-2:] == "GB":
                data_size = data_size[:-2]
                if data_renewal.upper() == "/DAY":
                    data_renewal = "Daily"
                elif data_renewal.upper() == "DATA":
                    data_renewal = "Data"
                else:
                    raise ValueError(f"Unknown: {data_renewal = }")
            else:
                data_size = -1  # "Unlimited" data case
                assert data_renewal.lower() == "unlimited"
            df.at[i, df.columns[2]] = float(data_size)
            df.at[i, df.columns[3]] = data_renewal.title()
        dfs["names"].append(sheet_name)
        dfs["pd"].append(df)
    return dfs


# %%
def grab_vi(driver):
    elems = driver.find_elements(By.CLASS_NAME, 
                "recg_revamp_packdetails")
    dfs = { # The names of the plans (spreadsheet) and their content
        "names": [],
        "pd": [],
    }
    for elem in elems:
        if 'd-none' in elem.get_attribute("class").split():
            continue
        sheet_name = elem.find_element(By.CLASS_NAME, 
                                    "pack-title").text.title()
        df = pd.DataFrame(columns=sheet_columns)
        plans = elem.find_elements(By.CLASS_NAME, "orc_cardtopsec")
        i = 0
        for plan in plans:
            # Cost of plan
            cost = plan.find_element(By.CLASS_NAME, "orc_mrp").text
            # Validity
            pack_validity = plan.find_element(By.CLASS_NAME, 
                                    "orcvalidityval").text.title()
            if pack_validity == '':
                continue
            pack_dur, pack_val_unit = pack_validity.split()
            if pack_val_unit.startswith("Hour"):
                pack_dur = float(pack_dur) / 24 # Hours to days
            elif pack_val_unit.startswith("Month"):
                pack_dur = float(pack_dur) * 28 # Months to days
            elif not pack_val_unit.startswith("Day"):
                raise ValueError(f"Unknown unit {pack_val_unit = }")
            # Data
            data_val = plan.find_element(By.CLASS_NAME, 
                            "orcdataval").text.split("/")
            if data_val[0] == '':
                continue
            data_size, data_renewal = -1, None
            if len(data_val) == 1:  # Data pack
                data_val = data_val[0]
                if data_val.title() == "Unlimited":
                    data_size = -1
                    data_renewal = "Unlimited"
                else:
                    data_size = data_val
                    data_renewal = "Data"
            else:
                data_size, data_renewal = data_val
                assert data_renewal == "Day"
                data_renewal = "Daily"
            if data_renewal != "Unlimited":
                data_size_unit = data_size[-2:]
                if data_size_unit == "MB":  # Need in GB
                    data_size = float(data_size[:-2]) / 1024
                elif data_size_unit == "GB":
                    data_size = float(data_size[:-2])
                elif data_size == "Night Free":
                    # Unlimited data from 12 am to 6 am; don't need
                    data_size = -1
                    data_renewal = "Unlimited (night)"
                else:
                    raise ValueError(f"Unknown {data_size_unit = }")
            # Log everything
            df.at[i, df.columns[0]] = int(cost)
            df.at[i, df.columns[1]] = float(pack_dur)
            df.at[i, df.columns[2]] = float(data_size)
            df.at[i, df.columns[3]] = data_renewal.title()
            i += 1
        dfs["names"].append(sheet_name)
        dfs["pd"].append(df)
    return dfs

# %%
def analyze_data(provider, sheet_num):
    if sheet_num == -1:
        if provider == "airtel":
            sheet_num = 0
        elif provider == "vi":
            sheet_num = 2
        else:
            raise ValueError(f"No default for {provider = }")
    # Now analyse the packs and list them in ascending order of price
    data_renewals = ["Daily", "Data"]
    # Read the data dump
    all_packs = pd.read_excel(f"./{provider}-packs.ods", 
                    sheet_name=None)    # All sheets
    pack = list(all_packs.keys())[sheet_num]  # The sheet to analyse
    packs = all_packs[pack]
    del packs["Unnamed: 0"]
    print(f"Found {len(packs)} packs for '{pack}'")
    # See all data methods
    for data_renewal in data_renewals:
        # Filter data renewal option
        packs_f = packs[packs["Data Renewal"] == data_renewal].copy()
        del packs_f["Data Renewal"]
        packs_f["Daily Cost (INR / Day)"] = packs_f["Cost (INR)"] /\
                                            packs_f["Validity (Days)"]
        # Sort by daily cost
        packs_sorted = packs_f.sort_values(by="Daily Cost (INR / Day)")
        if data_renewal == "Daily":
            print("Packs with daily data renewal")
        else:
            print("Packs with no data renewal (fixed quota)")
        print(packs_sorted)


# %%
def main(args: LocalArgs):
    print(f"Argument: {args}")
    # Sanity check 
    if args.net_provider not in web_addrs:
        raise NotImplementedError(f"Provider: {args.net_provider = }")
    # Initialize driver
    driver = webdriver.Chrome()
    web_addr = web_addrs[args.net_provider]
    # Load webpage
    driver.get(web_addr)
    driver.implicitly_wait(2)   # Max timeout of 2 sec
    if args.net_provider == "airtel":
        dfs = grab_airtel(driver)
    elif args.net_provider == "vi":
        dfs = grab_vi(driver)
    # End driver
    driver.quit()
    # Save to ODS file
    with pd.ExcelWriter(f"./{args.net_provider}-packs.ods") as writer:
        for sheet_name, df in zip(dfs["names"], dfs["pd"]):
            df.to_excel(writer, sheet_name=sheet_name)
    print("=========== Data Analysis ===========")
    analyze_data(args.net_provider, args.sheet_num)


if __name__ == "__main__" and "ipykernel" not in sys.argv[0]:
    try:
        start_time = time.time()
        args = tyro.cli(LocalArgs)
        main(args)
        end_time = time.time()
        print(f"Total time: {end_time - start_time:.3f} sec")
    except SystemExit as exc:
        print(f"System Exit: {exc}")
    except:
        traceback.print_exc()
    exit(0)


# %%
# Experimental section

# %%
web_addrs_ = {
    "airtel": "https://www.airtel.in/recharge-online",
    "vi": "https://www.myvi.in/prepaid/online-mobile-recharge",
    "jio": "https://www.jio.com/selfcare/plans/mobility/prepaid-plans-list/"
}
driver = webdriver.Chrome()
web_addr = web_addrs_["jio"]
driver.get(web_addr)
driver.implicitly_wait(2)

# %%
def grab_jio(driver):
    dfs = { # The names of the plans (spreadsheet) and their content
        "names": [],
        "pd": [],
    }
    sidebar_elem = driver.find_element(By.CLASS_NAME, 
                                        "simplebar-content")
    plan_buttons = sidebar_elem.find_elements(By.TAG_NAME, "button")
    plan_sheets = ["Popular Plans", "Data Packs", "JioPhone"]
    for plan_button in plan_buttons:
        if plan_button.text not in plan_sheets:
            # Not paying focus on these plans
            continue
        plan_button.click()
        print(plan_button.text)
        # Each plan sheet has many categories for packs
        elems = driver.find_elements(By.ID, "ISDContainer")
        for elem in elems:
            packs_header = elem.find_element(By.CLASS_NAME, 
                                        "j-accordion-panel")
            packs_header_title = packs_header.find_element(By.CLASS_NAME,
                                        "j-listBlock__block-text")
            header_title = packs_header_title.text
            print(f"--> {header_title}")
            if header_title.find("Plans") != -1:
                header_title = header_title[:\
                                        header_title.find("Plans")-1]
            else:
                header_title = header_title[:\
                                        header_title.find("(")-1]
            if header_title == "Top Trending":
                # Other categories will have this
                if packs_header.get_attribute("aria-expanded") \
                        == "true":
                    packs_header_title.click()  # Close it
                continue
            print(f"----> {header_title}")
            # Expand category
            if packs_header.get_attribute("aria-expanded") == "false":
                pass

grab_jio(driver)

# %%
dfs = { # The names of the plans (spreadsheet) and their content
    "names": [],
    "pd": [],
}
sidebar_elem = driver.find_element(By.CLASS_NAME, 
                                    "simplebar-content")
plan_buttons = sidebar_elem.find_elements(By.TAG_NAME, "button")
plan_sheets = ["Popular Plans", "JioPhone", "Data Packs"]
plan_sheets = ["Popular Plans"]
for plan_button in plan_buttons:
    if plan_button.text not in plan_sheets:
        # Not paying focus on these plans
        continue
    print(plan_button.text)
    ActionChains(driver).click(plan_button).perform()
    # Each plan sheet has many categories for packs
    elems = driver.find_elements(By.ID, "ISDContainer")
    for elem in elems:
        packs_header = elem.find_element(By.CLASS_NAME, 
                                    "j-accordion-panel")
        packs_header_title = packs_header.find_element(By.CLASS_NAME,
                                    "j-listBlock__block-text")
        header_title = packs_header_title.text
        if header_title.find("Plans") != -1:
            header_title = header_title[:header_title.find("Plans")-1]
        else:
            header_title = header_title[:header_title.find("(")-1]
        if header_title == "Top Trending":
            # Don't need to see summary over entire data
            continue
        print(f"----> {header_title}")
        # Expand category
        if packs_header.get_attribute("aria-expanded") == "false":
            ActionChains(driver).click(packs_header_title).perform()
        packs_grid = packs_header.find_element(By.CLASS_NAME,
                                    "j-accordion-panel__inner")


# %%

