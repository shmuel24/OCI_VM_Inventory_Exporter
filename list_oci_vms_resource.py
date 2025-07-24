import oci
import csv
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

ALL_VMS_CSV = "all_vms.csv"
SUMMARY_CSV = "summary.csv"
ERROR_LOG = "error.log"

def get_subscribed_regions(identity_client):
    return [r.region_name for r in identity_client.list_region_subscriptions(tenancy_id).data]

def list_vms_via_search(region, base_config, log_file):
    config = base_config.copy()
    config["region"] = region
    compute_client = oci.core.ComputeClient(config)
    search_client = oci.resource_search.ResourceSearchClient(config)

    instances_info = []
    try:
        print(f" [{region}] Searching for instances...")
        search_details = oci.resource_search.models.StructuredSearchDetails(
            query="query instance resources",
            type="Structured"
        )
        results = search_client.search_resources(search_details).data.items
    except Exception:
        log_file.write(f"[{region}] Resource search failed:\n{traceback.format_exc()}\n")
        print(f"Error in region {region} (Resource Search failed)")
        return []

    for item in results:
        try:
            instance = compute_client.get_instance(item.identifier).data
            if instance.lifecycle_state != "TERMINATED":
                shape = instance.shape
                ocpus = instance.shape_config.ocpus if instance.shape_config else 0
                memory = instance.shape_config.memory_in_gbs if instance.shape_config else 0
                instances_info.append({
                    "region": region,
                    "compartment_id": instance.compartment_id,
                    "display_name": instance.display_name,
                    "shape": shape,
                    "ocpus": ocpus,
                    "memory": memory,
                    "availability_domain": instance.availability_domain
                })
        except Exception:
            log_file.write(f"[{region}] Failed to get instance details for OCID: {item.identifier}\n{traceback.format_exc()}\n")
            print(f"Error retrieving instance in {region}")

    print(f"Finished region: {region} ({len(instances_info)} instances)")
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
    # All VMs CSV
    headers = ["region", "compartment_id", "display_name", "shape", "ocpus", "memory", "availability_domain"]
    with open(ALL_VMS_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in instances:
            writer.writerow(row)

    # Summary CSV
    with open(SUMMARY_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["region", "shape", "count", "total_ocpus", "total_memory_gb"])
        for (region, shape), data in summary_data.items():
            writer.writerow([region, shape, data["count"], data["ocpus"], data["memory"]])

if __name__ == "__main__":
    config = oci.config.from_file()
    tenancy_id = config["tenancy"]

    print("Authenticating...")
    identity_client = oci.identity.IdentityClient(config)

    print("Fetching subscribed regions...")
    regions = get_subscribed_regions(identity_client)

    all_instances = []
    print(f"Launching parallel resource search across {len(regions)} regions...\n")
    with ThreadPoolExecutor(max_workers=8) as executor, open(ERROR_LOG, "w") as log_file:
        futures = {
            executor.submit(list_vms_via_search, region, config, log_file): region
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

    print(f"Exporting CSVs to: {ALL_VMS_CSV}, {SUMMARY_CSV}")
    export_csv(all_instances, summary)

    print(f"\n Done. {len(all_instances)} VMs exported.")
    print(f"Errors (if any) logged to: {ERROR_LOG}")
