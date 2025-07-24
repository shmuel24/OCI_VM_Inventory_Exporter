# OCI VM Inventory Exporter

This is a lightweight and fast Python script that scans all **running Compute instances** (VMs) across **all subscribed regions** in your Oracle Cloud Infrastructure (OCI) tenancy.

It exports two CSV files:

* `all_vms.csv`: Full list of all VM instances with OCPU and memory details
* `summary.csv`: Aggregated OCPU and memory usage grouped by region and shape

---

## ✨ Features

* Cross-region scan using `resource_search`
* Parallel processing for faster results
* Clean CSV output
* Detailed error logging to `error.log`
* No resource modification — **read-only tool**

---

## Requirements

* Python 3.6 or higher
* OCI Python SDK (`oci`)

You can install it globally or use a virtual environment (recommended).

---

## Environment Setup

### Option 1: Global Install

```bash
pip install oci
```

### Option 2: With `virtualenv` (Recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## OCI Configuration

Before using the script, ensure you have a valid OCI config file.

### Step 1: Run OCI CLI Setup

```bash
oci setup config
```

This will create the file:

```bash
~/.oci/config
```

### Step 2: Grant Required Permissions

Your user or group must have access to:

* `RESOURCE_INSPECT` on `instance` resources
* `inspect` permission for `resource-search`
* `read` on compartments (if using restricted policies)

A basic example policy:

```
Allow group MyGroup to inspect instance-resources in tenancy
```

---

## Usage

### Step 1: Run the script

```bash
python3 list_oci_vms_summary_search_csv.py
```

### Step 2: Review the output files

| File          | Description                                                   |
| ------------- | ------------------------------------------------------------- |
| `all_vms.csv` | List of all non-terminated VMs across all regions             |
| `summary.csv` | Aggregated summary by region and shape                        |
| `error.log`   | Full stack traces for regions or resources with access issues |

---

## Sample Output

### `all_vms.csv`

| region         | compartment\_id          | display\_name | shape               | ocpus | memory | availability\_domain |
| -------------- | ------------------------ | ------------- | ------------------- | ----- | ------ | -------------------- |
| eu-frankfurt-1 | ocid1.compartment.oc1... | web-01        | VM.Standard.E4.Flex | 2     | 16     | EU-FRANKFURT-1-AD-1  |
| eu-frankfurt-1 | ocid1.compartment.oc1... | db-02         | VM.Standard.E4.Flex | 4     | 32     | EU-FRANKFURT-1-AD-2  |

### `summary.csv`

| region         | shape               | count | total\_ocpus | total\_memory\_gb |
| -------------- | ------------------- | ----- | ------------ | ----------------- |
| eu-frankfurt-1 | VM.Standard.E4.Flex | 2     | 6            | 48                |

---

## Notes

* Only **running or starting instances** are included
* Terminated VMs are automatically excluded
* Skips regions with access errors and logs them to `error.log`

---

## Repository Structure

```text
.
├── list_oci_vms_summary_search_csv.py   # Main script
├── requirements.txt                     # Required Python packages
├── README.md                            # This file
```

---

## ⚠️ Disclaimer

This tool is provided **as-is without any warranty**.

By using this script:

* You take full responsibility for verifying its behavior and output.
* The creator holds **no liability** for any actions, consequences, or damages caused directly or indirectly by using this tool.
* Always test in a safe environment before using in production or at scale.
