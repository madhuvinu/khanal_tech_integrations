#################################################################################################################################
################                 Only to Update the unicommerce live db data in the local database              #################
#################################################################################################################################




import frappe
import requests
import json
# === CONFIG ===
source_url = "https://khanaltech.com"
source_api_key = "05611a8cd92e189"
source_api_secret = "1189b9fe3ac34f6"
doctypes_to_copy = ["Unicommerce Orders"]
child_table_field = "order_line_items"  # Fieldname in the parent DocType
after_date = "2025-06-31"
page_limit = 1000
# === END CONFIG ===
def replicate_live_data():
    for doctype in doctypes_to_copy:
        print(f"🧹 Deleting all local {doctype} records")
        local_docs = frappe.get_all(doctype, fields=["name"])
        for doc in local_docs:
            frappe.delete_doc(doctype, doc.name, force=1, ignore_permissions=True)
        print(f"✅ Deleted {len(local_docs)} local records")
        headers = {
            "Authorization": f"token {source_api_key}:{source_api_secret}"
        }
        print(f"\n📥 Fetching filtered records from LIVE: {doctype}")
        total_synced = 0
        start = 0
        while True:
            try:
                res = requests.get(
                    f"{source_url}/api/resource/{doctype}",
                    headers=headers,
                    params={
                        "limit_page_length": page_limit,
                        "limit_start": start,
                        "filters": json.dumps([["creation", ">", after_date]]),
                        "fields": json.dumps(["name"])
                    },
                    timeout=60
                )
                data = res.json()
                names = [d["name"] for d in data.get("data", [])]
                if not names:
                    break
                for name in names:
                    try:
                        doc_res = requests.get(
                            f"{source_url}/api/resource/{doctype}/{name}",
                            headers=headers,
                            timeout=60
                        )
                        if doc_res.status_code != 200:
                            print(f"❌ Skipping {name}, HTTP {doc_res.status_code}")
                            continue
                        full_doc = doc_res.json()["data"]
                        full_doc["name"] = name
                        for field in ["modified_by", "owner", "creation", "modified", "docstatus"]:
                            full_doc.pop(field, None)
                        child_items = full_doc.get(child_table_field, [])
                        if not isinstance(child_items, list):
                            print(f"⚠️ No valid child table in {name}")
                            full_doc[child_table_field] = []
                        else:
                            full_doc[child_table_field] = child_items
                        frappe.get_doc(full_doc).insert(ignore_permissions=True)
                        print(f"✅ Synced {name} with {len(child_items)} line items")
                        total_synced += 1
                    except Exception as e:
                        print(f"❌ Failed syncing {name}: {str(e)}")
                if len(names) < page_limit:
                    break  # We've reached the last page
                else:
                    start += page_limit
            except Exception as fetch_err:
                print(f"❌ Error fetching from live: {str(fetch_err)}")
                break
        print(f"\n🎉 Total {doctype} synced: {total_synced}")

#!bench --site dev.localhost execute khanal_tech_integrations.utils.unicommerceFile.Replicate_khanaltech.replicate_live_data 