import oci
import csv
import traceback
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

ALL_VMS_CSV = "all_vms.csv"
SUMMARY_CSV = "summary.csv"
ERROR_LOG = "error.log"

def list_all_compartments(identity_client, tenancy_id):
    compartments = oci.pagination.list_call_get_all_results(
        identity_client.list_compartments,
        compartment_id=tenancy_id,
        compartment_id_in_subtree=True,
        access_level="ANY"
    ).data
    active_comps = [c for c in compartments if c.lifecycle_state == "ACTIVE"]
    active_comps.append(oci.identity.models.Compartment(id=tenancy_id, name="root"))
    return active_comps

def list_vms_in_region(region, base_config, compartments, log_file, verbose=False):
    config = base_config.copy()
    config["region"] = region
    compute_client = oci.core.ComputeClient(config)

    instances_info = []

    print(f"🔍 [{region}] Scanning {len(compartments)} compartments...")
    for comp in compartments:
        try:
            instances = oci.pagination.list_call_get_all_results(
                compute_client.list_instances,
                compartment_id=comp.id
            ).data
        except Exception:
            log_file.write(f"[{region}] Compartment {comp.name} ({comp.id}) failed:\n{traceback.format_exc()}\n")
            print(f"rror in compartment {comp.name} ({region})")
            continue

        for instance in instances:
            if instance.lifecycle_state != "TERMINATED":
                shape = instance.shape
                ocpus = instance.shape_config.ocpus if instance.shape_config else 0
                memory = instance.shape_config.memory_in_gbs if instance.shape_config else 0

                if verbose:
                    print(f"[{region}] {comp.name} → {instance.display_name} | {shape} | {ocpus} OCPU | {memory} GB")

                instances_info.append({
                    "region": region,
                    "compartment_id": comp.id,
                    "compartment_name": comp.name,
                    "display_name": instance.display_name,
                    "shape": shape,
                    "ocpus": ocpus,
                    "memory": memory,
                    "availability_domain": instance.availability_domain
                })

    print(f"Finished region: {region} ({len(instances_info)} VMs)")
    return instances_info

def summarize(instances):
    summary = defaultdict(lambda: {"ocpus": 0, "memory": 0, "count": 0})
    for inst in instances:
        key = (inst['region'], inst['shape'])
        summary[key]["ocpus"] += inst["ocpus"]
        summary[key]["memory"] += inst["memory"]
        summary[key]["count"] += 1
    return summary

def export_csv(instances, summary_data):
    headers = [
        "region", "compartment_id", "compartment_name", "display_name",
        "shape", "ocpus", "memory", "availability_domain"
    ]
    with open(ALL_VMS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in instances:
            writer.writerow(row)

    with open(SUMMARY_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["region", "shape", "count", "total_ocpus", "total_memory_gb"])
        for (region, shape), data in summary_data.items():
            writer.writerow([region, shape, data["count"], data["ocpus"], data["memory"]])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Accurate OCI VM Inventory Exporter using list_instances()",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--region", help="Only scan this region (optional)")
    parser.add_argument("--profile", default="DEFAULT", help="OCI CLI profile to use (default: DEFAULT)")
    parser.add_argument("--compartment-id", help="Scan only a specific compartment OCID (optional)")
    parser.add_argument("--verbose", action="store_true", help="Print each discovered VM to the screen")
    args = parser.parse_args()

    config = oci.config.from_file(profile_name=args.profile)
    tenancy_id = config["tenancy"]
    identity_client = oci.identity.IdentityClient(config)

    print("Fetching compartments from home region...")
    all_compartments = list_all_compartments(identity_client, tenancy_id)

    if args.compartment_id:
        filtered = [c for c in all_compartments if c.id == args.compartment_id]
        if not filtered:
            print(f"Compartment ID not found or not accessible: {args.compartment_id}")
            exit(1)
        compartments = filtered
        print(f"Scanning only compartment: {filtered[0].name} ({filtered[0].id})")
    else:
        compartments = all_compartments

    if args.region:
        regions = [args.region]
        print(f"Scanning single region: {args.region}")
    else:
        print("Fetching all subscribed regions...")
        regions = [r.region_name for r in identity_client.list_region_subscriptions(tenancy_id).data]

    all_instances = []
    print(f"Starting scan across {len(regions)} region(s)...\n")
    with ThreadPoolExecutor(max_workers=8) as executor, open(ERROR_LOG, "w") as log_file:
        futures = {
            executor.submit(list_vms_in_region, region, config, compartments, log_file, args.verbose): region
            for region in regions
        }
        for future in as_completed(futures):
            region = futures[future]
            try:
                region_instances = future.result()
                all_instances.extend(region_instances)
            except Exception:
                log_file.write(f"[{region}] Unexpected region-level error:\n{traceback.format_exc()}\n")
                print(f"Unexpected error in region {region}")

    print("\n Creating summary...")
    summary = summarize(all_instances)

    print(f"Exporting to {ALL_VMS_CSV} and {SUMMARY_CSV}...")
    export_csv(all_instances, summary)

    print(f"\n Done. {len(all_instances)} VMs exported.")
    print(f"Errors (if any) logged to: {ERROR_LOG}")
