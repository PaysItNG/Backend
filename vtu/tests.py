def get_vtpass_data():
    # Simulated API call
    return [
        {"network": "MTN", "variation_code": "mtn1gb", "amount": "300", "name": "1GB Data"},
        {"network": "MTN", "variation_code": "mtn2gb", "amount": "500", "name": "2GB Data"},
    ]

def get_providerx_data():
    # Simulated API call
    return [
        {"carrier": "MTN", "plan_id": "mtn_daily_1gb", "price": 290, "size": "1GB"},
        {"carrier": "MTN", "plan_id": "mtn_daily_2gb", "price": 490, "size": "2GB"},
    ]

def normalize_vtpass(plan):
    return {
        "network": plan["network"],
        "qty": plan["name"].split()[0],  # "1GB"
        "price": float(plan["amount"]),
        "provider": "vtpass",
        "plan_id": plan["variation_code"]
    }

def normalize_providerx(plan):
    return {
        "network": plan["carrier"],
        "qty": plan["size"],
        "price": float(plan["price"]),
        "provider": "providerx",
        "plan_id": plan["plan_id"]
    }

vtpass = list(map(normalize_vtpass, get_vtpass_data()))
providerx = list(map(normalize_providerx, get_providerx_data()))

# Combine them
all_data_plans = vtpass + providerx

# Optionally sort by price
sorted_plans = sorted(all_data_plans, key=lambda x: (x["network"], x["qty"], x["price"]))

for plan in sorted_plans:
    print(plan)