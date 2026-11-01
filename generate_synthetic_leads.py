import random
import datetime
import pandas as pd
import numpy as np
import os

# Fix seed for reproducible, high quality realistic dataset
random.seed(42)
np.random.seed(42)

first_names = [
    "Aarav", "Aditi", "Ajay", "Amit", "Ananya", "Ankit", "Arun", "Bhavna", "Chetan", "Deepa",
    "Divya", "Ganesh", "Gayatri", "Harish", "Isha", "Jayant", "Kavita", "Kiran", "Karthik", "Lakshmi",
    "Manish", "Meera", "Manoj", "Neha", "Nikhil", "Nisha", "Pradeep", "Pooja", "Prakash", "Priya",
    "Rahul", "Rajesh", "Ramesh", "Ritu", "Rohan", "Sandhya", "Sanjay", "Shalini", "Shreya", "Siddharth",
    "Sneha", "Subhash", "Suresh", "Swati", "Tanvi", "Varun", "Vikas", "Vikram", "Vinay", "Vivek"
]

last_names = [
    "Agarwal", "Bhat", "Chatterjee", "Deshmukh", "Fernandes", "Gupta", "Hegde", "Iyer", "Jain", "Joshi",
    "Kapoor", "Kulkarni", "Kumar", "Malhotra", "Mehta", "Menon", "Mishra", "Mukherjee", "Nair", "Patel",
    "Pillai", "Prabhu", "Ranganathan", "Rao", "Reddy", "Saxena", "Sen", "Sharma", "Shetty", "Singh",
    "Singhania", "Srinivasan", "Subramanian", "Trivedi", "Varma", "Verma", "Venkatesh", "Wadhwa", "Yadav", "Zaveri"
]

cities = ["Bangalore", "Hyderabad", "Chennai", "Mumbai", "Pune", "Delhi NCR"]

lead_sources = [
    "Website Inquiry", "Instagram Ad", "Google Search", 
    "Architect Referral", "Past Client Referral", "Walk-in Studio", 
    "Facebook Campaign", "Housing Portal"
]

budget_ranges = [
    "Below ₹3 lakh",
    "₹3 lakh–₹5 lakh",
    "₹5 lakh–₹10 lakh",
    "₹10 lakh–₹25 lakh",
    "Above ₹25 lakh"
]

project_types = [
    "1BHK",
    "2BHK",
    "3BHK",
    "Villa",
    "Modular Kitchen",
    "Commercial/Office"
]

property_statuses = [
    "Ready to Move",
    "Possession within 30 days",
    "Possession within 1–3 months",
    "Under Construction"
]

project_timelines = [
    "Immediately",
    "Within 1 month",
    "Within 3 months",
    "Within 6 months",
    "Just Exploring"
]

scopes_of_work = [
    "Full Turnkey Interior",
    "Modular Kitchen",
    "Wardrobe",
    "Renovation",
    "Furniture and Woodwork",
    "Commercial Interiors"
]

purchase_readiness_options = [
    "Ready to Start",
    "Comparing Vendors",
    "Budget Planning",
    "Just Exploring"
]

preferred_contact_methods = [
    "Phone Call",
    "WhatsApp",
    "Email",
    "In-Person Consultation"
]

lead_statuses = [
    "New",
    "Qualified",
    "Follow-up",
    "Converted",
    "Lost"
]

# Requirement templates tailored by Project Type & Scope
requirements_templates = {
    "Villa": [
        "Complete luxury interior for duplex villa; Italian marble, automation, walk-in closets, and false ceiling with cove lighting.",
        "4-bedroom villa interior with modern neo-classical accents, custom wood panelling, and designer landscaped patio.",
        "Turnkey design for gated community villa; modular kitchen with island, study room library, and terrace lounge."
    ],
    "3BHK": [
        "Contemporary Scandinavian theme for 3BHK flat; acrylic modular kitchen, master walk-in wardrobe, and TV unit.",
        "Warm minimalist 3BHK interior with fluted wall panels, bar unit, false ceiling, and kids study unit.",
        "Full home woodwork and electrical layout for newly handed over 3BHK apartment."
    ],
    "2BHK": [
        "Space-saving 2BHK interior solution with modular storage, hydraulic bed, and functional compact kitchen.",
        "Modern urban aesthetic for 2BHK apartment; laminate finish wardrobes, breakfast counter, and wallpaper accents.",
        "Budget-conscious 2BHK furnishing with modular kitchen, sliding wardrobes, and balcony garden setup."
    ],
    "1BHK": [
        "Compact 1BHK space-efficient modular furniture, convertible sofa-bed, and sleek parallel kitchen.",
        "Modern 1BHK interior for rental investment property; durable laminates and low-maintenance fittings."
    ],
    "Modular Kitchen": [
        "L-shaped modular kitchen with marine grade HDHMR ply, Blum soft-close fittings, and quartz countertop.",
        "Parallel kitchen layout with tall pantry unit, wicker baskets, built-in microwave slot, and chimney ducting.",
        "Renovation of existing 10-year-old kitchen into an open-concept modern modular island kitchen."
    ],
    "Commercial/Office": [
        "Boutique legal firm office setup: 12 workstations, 2 director cabins, conference room, and reception desk.",
        "Co-working office space interior with acoustic baffle ceiling, breakout zone, and ergonomic hot-desks.",
        "Retail showroom display interior with track lights, display pedestals, and billing counter."
    ]
}

def generate_leads(n=250):
    leads = []
    start_date = datetime.date(2026, 7, 1)
    end_date = datetime.date(2026, 10, 31)
    delta_days = (end_date - start_date).days

    for i in range(1, n + 1):
        lead_id = f"SHA-2026-{i:04d}"
        fname = random.choice(first_names)
        lname = random.choice(last_names)
        cust_name = f"{fname} {lname}"
        
        # Safe fictional phone format (using designated test range 91234 00000 - 91234 00999)
        phone = f"+91 91234 {i+10000:05d}"
        email = f"{fname.lower()}.{lname.lower()}{i}@example.com"
        
        city = random.choice(cities)
        source = random.choices(
            lead_sources, 
            weights=[25, 20, 18, 12, 10, 7, 5, 3], 
            k=1
        )[0]
        
        p_type = random.choices(
            project_types,
            weights=[10, 35, 30, 12, 8, 5],
            k=1
        )[0]
        
        # Correlate budget logically with project type
        if p_type == "Villa":
            b_range = random.choices(budget_ranges, weights=[0, 0, 5, 45, 50], k=1)[0]
            scope = random.choices(scopes_of_work, weights=[60, 5, 5, 10, 20, 0], k=1)[0]
        elif p_type == "Commercial/Office":
            b_range = random.choices(budget_ranges, weights=[2, 5, 25, 45, 23], k=1)[0]
            scope = "Commercial Interiors"
        elif p_type == "Modular Kitchen":
            b_range = random.choices(budget_ranges, weights=[15, 50, 30, 5, 0], k=1)[0]
            scope = "Modular Kitchen"
        elif p_type == "3BHK":
            b_range = random.choices(budget_ranges, weights=[2, 8, 45, 40, 5], k=1)[0]
            scope = random.choices(scopes_of_work, weights=[45, 15, 15, 15, 10, 0], k=1)[0]
        elif p_type == "2BHK":
            b_range = random.choices(budget_ranges, weights=[10, 35, 45, 10, 0], k=1)[0]
            scope = random.choices(scopes_of_work, weights=[40, 20, 20, 10, 10, 0], k=1)[0]
        else: # 1BHK
            b_range = random.choices(budget_ranges, weights=[35, 45, 20, 0, 0], k=1)[0]
            scope = random.choices(scopes_of_work, weights=[30, 25, 25, 10, 10, 0], k=1)[0]
            
        prop_status = random.choices(
            property_statuses,
            weights=[35, 25, 25, 15],
            k=1
        )[0]
        
        # Timeline correlated with property status
        if prop_status == "Ready to Move":
            timeline = random.choices(project_timelines, weights=[45, 35, 15, 5, 0], k=1)[0]
            readiness = random.choices(purchase_readiness_options, weights=[50, 30, 15, 5], k=1)[0]
        elif prop_status == "Possession within 30 days":
            timeline = random.choices(project_timelines, weights=[25, 50, 20, 5, 0], k=1)[0]
            readiness = random.choices(purchase_readiness_options, weights=[35, 45, 15, 5], k=1)[0]
        elif prop_status == "Possession within 1–3 months":
            timeline = random.choices(project_timelines, weights=[5, 25, 50, 15, 5], k=1)[0]
            readiness = random.choices(purchase_readiness_options, weights=[20, 40, 30, 10], k=1)[0]
        else: # Under Construction
            timeline = random.choices(project_timelines, weights=[0, 5, 20, 50, 25], k=1)[0]
            readiness = random.choices(purchase_readiness_options, weights=[10, 25, 40, 25], k=1)[0]
            
        contact_method = random.choice(preferred_contact_methods)
        
        # Correlate lead status with readiness
        if readiness == "Ready to Start":
            status = random.choices(lead_statuses, weights=[15, 35, 25, 20, 5], k=1)[0]
        elif readiness == "Comparing Vendors":
            status = random.choices(lead_statuses, weights=[20, 30, 35, 10, 5], k=1)[0]
        elif readiness == "Budget Planning":
            status = random.choices(lead_statuses, weights=[30, 20, 35, 5, 10], k=1)[0]
        else: # Just Exploring
            status = random.choices(lead_statuses, weights=[40, 10, 25, 2, 23], k=1)[0]
            
        # Select realistic requirements description
        req_list = requirements_templates.get(p_type, ["Custom interior woodwork and furnishing requirements."])
        customer_req = random.choice(req_list)
        
        # Random date
        random_days = random.randint(0, delta_days)
        created_date = (start_date + datetime.timedelta(days=random_days)).isoformat()
        
        leads.append({
            "Lead_ID": lead_id,
            "Customer_Name": cust_name,
            "Phone": phone,
            "Email": email,
            "Lead_Source": source,
            "City": city,
            "Budget_Range": b_range,
            "Project_Type": p_type,
            "Property_Status": prop_status,
            "Project_Timeline": timeline,
            "Scope_of_Work": scope,
            "Customer_Requirements": customer_req,
            "Purchase_Readiness": readiness,
            "Preferred_Contact_Method": contact_method,
            "Lead_Status": status,
            "Created_Date": created_date
        })

    return pd.DataFrame(leads)

df_synthetic = generate_leads(250)

# Save to data/synthetic/interior_design_leads.csv
synthetic_path = os.path.join("data", "synthetic", "interior_design_leads.csv")
df_synthetic.to_csv(synthetic_path, index=False)
print(f"Generated {len(df_synthetic)} synthetic records.")
print(f"Saved synthetic leads to: {synthetic_path}")

# Validation checks
assert len(df_synthetic) >= 200, "Must have at least 200 records"
assert df_synthetic["Lead_ID"].nunique() == len(df_synthetic), "Lead_ID must be unique"
assert df_synthetic.isna().sum().sum() == 0, "No unintended missing values allowed"
print("All assertions passed successfully!")
