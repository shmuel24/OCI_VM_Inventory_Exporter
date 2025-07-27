# OCI VM Inventory Exporter

This is a Python script that scans all **running Compute instances** (VMs) across **all compartments and subscribed regions** in your Oracle Cloud Infrastructure (OCI) tenancy using the `list_instances()` method for full accuracy.

It exports two CSV files:

* `all_vms.csv`: Full list of all VM instances with OCPU, memory, and compartment details
* `summary.csv`: Aggregated OCPU and memory usage grouped by region and shape

---

## ✨ Features

* Accurate VM discovery using `list_instances()` per compartment
* Scans all compartments (not relying on resource search)
* Parallel processing per region for fast execution
* Clean CSV output with `compartment_name` included
* Detailed error logging to `error.log`
* No resource modification — **read-only tool**
* Optional: restrict to a specific region with `--region`
* Optional: use a specific OCI profile with `--profile`
* Optional: scan only one compartment using `--compartment-id`
* Optional: enable debug-level instance logging with `--verbose`

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

* `inspect` on `instance-family` and `compartments`
* `read` on compartments

A basic example policy:

```
Allow group MyGroup to inspect instance-family in tenancy
Allow group MyGroup to inspect compartments in tenancy
```

---

## Usage

### Step 1: Run the script

```bash
python3 list_oci_vms_summary_compartments.py [--region REGION] [--profile PROFILE] [--compartment-id OCID] [--verbose]
```

### Step 2: Review the output files

| File          | Description                                                 |
| ------------- | ----------------------------------------------------------- |
| `all_vms.csv` | Full list of all non-terminated VMs with compartment info   |
| `summary.csv` | Aggregated summary by region and shape                      |
| `error.log`   | Full stack traces for compartments or regions with failures |

### Optional Flags

* `--region eu-frankfurt-1` → Only scan this region
* `--profile dev` → Use a custom profile from `~/.oci/config`
* `--compartment-id ocid1.compartment.oc1...` → Only scan one compartment
* `--verbose` → Print every discovered VM to the terminal

---

## Sample Output

### `all_vms.csv`

| region         | compartment\_id          | compartment\_name | display\_name | shape               | ocpus | memory | availability\_domain |
| -------------- | ------------------------ | ----------------- | ------------- | ------------------- | ----- | ------ | -------------------- |
| eu-frankfurt-1 | ocid1.compartment.oc1... | DevCompartment    | web-01        | VM.Standard.E4.Flex | 2     | 16     | EU-FRANKFURT-1-AD-1  |
| eu-frankfurt-1 | ocid1.compartment.oc1... | DevCompartment    | db-02         | VM.Standard.E4.Flex | 4     | 32     | EU-FRANKFURT-1-AD-2  |

### `summary.csv`

| region         | shape               | count | total\_ocpus | total\_memory\_gb |
| -------------- | ------------------- | ----- | ------------ | ----------------- |
| eu-frankfurt-1 | VM.Standard.E4.Flex | 2     | 6            | 48                |

---

## Notes

* Only **running or starting instances** are included
* Terminated VMs are automatically excluded
* All compartments are queried unless `--compartment-id` is used
* Errors are logged in `error.log` with full traceback

---

## Repository Structure

```text
.
├── list_oci_vms_summary_compartments.py  # Main script
├── requirements.txt                      # Required Python packages
├── README.md                             # This file
```

---

## ⚠️ Disclaimer

This tool is provided **as-is without any warranty**.

By using this script:

* You take full responsibility for verifying its behavior and output.
* The creator holds **no liability** for any actions, consequences, or damages caused directly or indirectly by using this tool.
* Always test in a safe environment before using in production or at scale.
