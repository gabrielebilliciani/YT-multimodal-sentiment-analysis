# configs/product_catalog.py

PRODUCTS_TO_ANALYZE = {
    "smartphones": [
        # --- Apple iPhones ---
        # Generation 1 (Most Recent)
        {"name": "iPhone 15 Pro Max", "brand": "Apple", "generation": "15 Pro Max", "year": 2023, "keywords_for_relevance": ["iPhone 15 Pro Max", "review", "camera", "battery"]},
        # Generation 2
        {"name": "iPhone 14 Pro Max", "brand": "Apple", "generation": "14 Pro Max", "year": 2022, "keywords_for_relevance": ["iPhone 14 Pro Max", "review", "dynamic island", "always on"]},
        # Generation 3
        {"name": "iPhone 13 Pro Max", "brand": "Apple", "generation": "13 Pro Max", "year": 2021, "keywords_for_relevance": ["iPhone 13 Pro Max", "review", "cinematic mode", "prores"]},
        # Generation 4
        {"name": "iPhone 12 Pro Max", "brand": "Apple", "generation": "12 Pro Max", "year": 2020, "keywords_for_relevance": ["iPhone 12 Pro Max", "review", "5G", "lidar"]},
        # Generation 5
        {"name": "iPhone 11 Pro Max", "brand": "Apple", "generation": "11 Pro Max", "year": 2019, "keywords_for_relevance": ["iPhone 11 Pro Max", "review", "triple camera", "night mode"]},

        # --- Samsung Galaxy Flagships ---
        # Generation 1 (Most Recent)
        {"name": "Samsung Galaxy S24 Ultra", "brand": "Samsung", "generation": "S24 Ultra", "year": 2024, "keywords_for_relevance": ["Galaxy S24 Ultra", "review", "AI features", "titanium"]},
        # Generation 2
        {"name": "Samsung Galaxy S23 Ultra", "brand": "Samsung", "generation": "S23 Ultra", "year": 2023, "keywords_for_relevance": ["Galaxy S23 Ultra", "review", "200MP camera", "snapdragon"]},
        # Generation 3
        {"name": "Samsung Galaxy S22 Ultra", "brand": "Samsung", "generation": "S22 Ultra", "year": 2022, "keywords_for_relevance": ["Galaxy S22 Ultra", "review", "S Pen built-in", "nightography"]},
        # Generation 4
        {"name": "Samsung Galaxy S21 Ultra", "brand": "Samsung", "generation": "S21 Ultra", "year": 2021, "keywords_for_relevance": ["Galaxy S21 Ultra", "review", "director's view", "space zoom"]},
        # Generation 5
        {"name": "Samsung Galaxy S20 Ultra", "brand": "Samsung", "generation": "S20 Ultra", "year": 2020, "keywords_for_relevance": ["Galaxy S20 Ultra", "review", "100x zoom", "120Hz display"]},
    ],

    "saas_crm": [
        {"name": "Salesforce Sales Cloud", "brand": "Salesforce", "type": "CRM", "search_language": "en", "category_tags": ["Enterprise CRM", "Sales Automation"], "keywords_for_relevance": ["Salesforce Sales Cloud review", "Salesforce features", "Salesforce pricing", "Salesforce comparison", "Salesforce demo"]},
        
        {"name": "HubSpot CRM Suite", "brand": "HubSpot", "type": "CRM", "search_language": "en", "category_tags": ["SMB CRM", "Inbound Marketing", "All-in-One CRM"], "keywords_for_relevance": ["HubSpot CRM review", "HubSpot Sales Hub features", "HubSpot Marketing Hub pricing", "HubSpot vs", "HubSpot demo"]},

        {"name": "Microsoft Dynamics 365 Sales", "brand": "Microsoft", "type": "CRM", "search_language": "en", "category_tags": ["Enterprise CRM", "Microsoft Ecosystem", "Sales Force Automation"], "keywords_for_relevance": ["Dynamics 365 Sales review", "Microsoft CRM features", "Dynamics 365 pricing", "Dynamics vs Salesforce", "Dynamics 365 demo", "MSFT D365 Sales"]},
        
        # {"name": "Zoho CRM", "brand": "Zoho", "type": "CRM", "search_language": "en", "category_tags": ["SMB CRM", "Value for Money CRM", "Zoho Ecosystem"], "keywords_for_relevance": ["Zoho CRM review", "Zoho One features", "Zoho CRM pricing", "Zoho vs HubSpot"]},
        
        # {"name": "Pipedrive", "brand": "Pipedrive", "type": "CRM", "search_language": "en", "category_tags": ["SMB CRM", "Sales Pipeline Focus", "User-Friendly CRM", "Activity-based selling"], "keywords_for_relevance": ["Pipedrive review", "Pipedrive features", "Pipedrive pricing", "Pipedrive vs HubSpot", "Pipedrive demo", "Pipedrive tutorial"]},
        
        # {"name": "Freshsales (Freshworks CRM)", "brand": "Freshworks", "type": "CRM", "search_language": "en", "category_tags": ["SMB CRM", "Customer Engagement", "AI-powered CRM", "Freshworks Suite"], "keywords_for_relevance": ["Freshsales review", "Freshworks CRM features", "Freshsales pricing", "Freshworks vs Zoho", "Freshsales demo", "Freshworks CRM tutorial"]},
        
        # {"name": "Monday.com Sales CRM", "brand": "Monday.com", "type": "CRM", "search_language": "en", "category_tags": ["SMB to Mid-Market CRM", "Visual CRM", "Workflow Automation", "Work OS"], "keywords_for_relevance": ["Monday Sales CRM review", "Monday.com CRM features", "Monday CRM pricing", "Monday.com vs Asana CRM", "Monday CRM demo", "Monday for sales teams"]},
        
        # {"name": "SAP Sales Cloud", "brand": "SAP", "type": "CRM", "search_language": "en", "category_tags": ["Enterprise CRM", "SAP Ecosystem", "Customer Experience (CX)"], "keywords_for_relevance": ["SAP Sales Cloud review", "SAP CRM features", "SAP C4C pricing", "SAP vs Salesforce", "SAP Sales Cloud demo", "SAP CX tutorial"]},
    ],
    # "laptops": [ ... ],
    # "cameras": [ ... ],
}