import argparse
import json

def display_profile():
    profile = {
        "business_name": "Integrated Avodah LLC",
        "category": "Religious organization",
        "description": "Integrated Avodah is a religious organization with a unique approach to fostering a vibrant global community and spiritual governance in Lawrence, KS.",
        "address": "2523 Redbud Ln, APT 16, Lawrence, KS 66046, US",
        "phone": "(785) 764-2680",
        "website": "https://www.integrated-avodah-llc.org/",
        "mission": "To provide foundational and structural support to chosen entities, creating strong, worldwide alliances built on complete communication and mandatory participation.",
        "governance_model": "Self-government where leaders are selected from within the community and rotate roles.",
        "brand_one_liner": "A holistic corporate compliance portal facilitating ethical stewardship and regulatory governance.",
        "core_values": ["Stewardship", "Integrity", "Compliance", "Holistic Service"],
        "concept": "Avodah: The integration of work, worship, and service to frame corporate compliance as a form of ethical stewardship.",
        "target_audiences": [
            "Compliance officers at mission-driven organizations requiring tools that reflect their specific ethical frameworks.",
            "Corporate legal departments seeking a streamlined, integrated approach to managing multi-jurisdictional regulatory demands."
        ]
    }
    
    print("==================================================")
    print("     INTEGRATED AVODAH LLC - PROFILE CONFIG       ")
    print("==================================================")
    for key, value in profile.items():
        if isinstance(value, list):
            print(f"\n[{key.upper()}]")
            for item in value:
                print(f"  - {item}")
        else:
            print(f"\n[{key.upper()}]:\n  {value}")
    print("\n==================================================")

def main():
    parser = argparse.ArgumentParser(
        description="Integrated Avodah LLC Command Line Management Utility"
    )
    parser.add_argument(
        "--profile", 
        action="store_true", 
        help="Display the core organizational profile and compliance parameters."
    )
    
    args = parser.parse_args()
    
    if args.profile:
        display_profile()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
