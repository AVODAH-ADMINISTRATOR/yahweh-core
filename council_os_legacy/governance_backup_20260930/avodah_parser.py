import argparse
import json

def main():
    parser = argparse.ArgumentParser(
        description="Integrated Avodah LLC Corporate Compliance Portal Parser"
    )
    parser.add_argument(
        '--profile', 
        action='store_true', 
        help='Display core business profile and contact attributes'
    )
    parser.add_argument(
        '--values', 
        action='store_true', 
        help='Display brand one-liner, core values, and conceptual overview'
    )
    args = parser.parse_args()

    # Data mapped strictly from authoritative source parameters
    avodah_data = {
        "business_name": "Integrated Avodah LLC",
        "category": "Religious organization",
        "description": "A religious organization with a unique approach to fostering a vibrant global community and spiritual governance in Lawrence, KS.",
        "address": "2523 Redbud Ln, APT 16, Lawrence, KS 66046, US",
        "phone": "(785) 764-2680",
        "one_liner": "A holistic corporate compliance portal facilitating ethical stewardship and regulatory governance.",
        "core_values": ["Stewardship", "Integrity", "Compliance", "Holistic Service"] ,
        "concept": "The concept of 'Avodah' represents the integration of work, worship, and service to frame corporate compliance as a form of ethical stewardship."
    }

    if args.profile:
        print("=== Integrated Avodah LLC Business Profile ===")
        print(f"Business Name: {avodah_data['business_name']}")
        print(f"Category: {avodah_data['category']}")
        print(f"Description: {avodah_data['description']}")
        print(f"Address: {avodah_data['address']}")
        print(f"Phone: {avodah_data['phone']}")
    elif args.values:
        print("=== Brand Identity & Core Values ===")
        print(f"Brand One-Liner: {avodah_data['one_liner']}")
        print(f"Core Values: {', '.join(avodah_data['core_values'])}")
        print(f"Concept Definition: {avodah_data['concept']}")
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
