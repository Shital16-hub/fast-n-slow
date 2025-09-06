# create_updated_service_docs.py - ALL SERVICE DOCUMENTS
"""
Creates properly formatted service documents for ALL roadside services
Simple, clear format that works with the simplified RAG system
"""
import asyncio
from pathlib import Path

def create_all_service_documents():
    """Create all service documents with clear, consistent formatting"""
    
    # Ensure services_docs directory exists
    services_dir = Path("services_docs")
    services_dir.mkdir(exist_ok=True)
    
    # All service documents with clear pricing
    service_docs = {
        "towing_service.txt": """SERVICE: Professional Towing Service
BASE_PRICE: 169
DESCRIPTION: Complete vehicle towing service using professional tow trucks with experienced certified operators for safe vehicle transport.
REQUIREMENTS: Vehicle to be towed, destination location, clear access for tow truck
TIME: 30-90 minutes depending on distance and conditions
PRICING_RULES:
- Hook Fee functional vehicle: $169
- Hook Fee non-functional vehicle: $189
- Short distance mileage rate: $8 per mile
- Long distance mileage rate: $10 per mile
- Standard mileage rate: $9 per mile
- Total cost: Hook Fee + (Mileage Rate × Distance)
WHAT_IS_INCLUDED: Vehicle hookup, safe transport, unhooking at destination, damage-free towing guarantee""",

        "battery_jumpstart.txt": """SERVICE: Jump Start Service
BASE_PRICE: 150
DESCRIPTION: Professional jump start service for dead vehicle batteries using commercial-grade equipment and testing.
REQUIREMENTS: Vehicle with dead battery, access to battery compartment, valid identification
TIME: 15-30 minutes
PRICING_RULES:
- Daytime service (7:00 AM - 7:00 PM): $150
- Nighttime service (7:00 PM - 7:00 AM): $200
- Multiple battery pricing: 2 batteries $229, 3 batteries $265, 4 batteries $295
- Service includes battery testing and basic electrical system check
WHAT_IS_INCLUDED: Battery testing, jump start service, basic electrical system check, battery condition assessment""",

        "tire_change_service.txt": """SERVICE: Tire Change and Replacement Service
BASE_PRICE: 165
DESCRIPTION: Professional tire change service including spare tire installation or new tire replacement with proper torque specifications.
REQUIREMENTS: Vehicle with flat or damaged tire, spare tire available or new tire for replacement, lug wrench access
TIME: 20-45 minutes
PRICING_RULES:
- Daytime service (7:00 AM - 7:00 PM): $165
- Nighttime service (7:00 PM - 7:00 AM): $200
- Tire replacement: add cost of new tire to service price
- Run-flat tire service: additional $25 surcharge
- Wheel lock removal: additional $35 if special key not available
WHAT_IS_INCLUDED: Tire removal, spare installation or new tire mounting, wheel torque to manufacturer specification, basic tire pressure check""",

        "lockout_service.txt": """SERVICE: Vehicle Lockout Service
BASE_PRICE: 150
DESCRIPTION: Professional non-destructive vehicle entry service when keys are locked inside vehicle using specialized locksmith tools.
REQUIREMENTS: Valid identification, proof of vehicle ownership, no keys accessible
TIME: 10-25 minutes
PRICING_RULES:
- Daytime service (7:00 AM - 7:00 PM): $150
- Nighttime service (7:00 PM - 7:00 AM): $200
- Emergency lockout (highway, blocking traffic): priority service, standard rates apply
- Luxury vehicle lockout: additional $50 surcharge for specialized tools
- Antique vehicle lockout: additional $75 surcharge and damage waiver required
WHAT_IS_INCLUDED: Non-destructive entry, lock manipulation, verification of vehicle ownership, basic door mechanism check""",

        "fuel_delivery_service.txt": """SERVICE: Emergency Fuel Delivery Service
BASE_PRICE: 199
DESCRIPTION: Emergency gasoline or diesel fuel delivery service for vehicles that have run out of fuel, includes sufficient fuel to reach nearest gas station.
REQUIREMENTS: Vehicle location, fuel type specification (regular, premium, diesel), accessible location for service vehicle
TIME: 20-40 minutes delivery time
PRICING_RULES:
- Base service fee: $199 plus cost of fuel
- Distance allowance: first 5 miles included in base price
- Additional mileage: $5 per mile for distances over 5 miles
- Total price if distance over 5 miles: $199 + fuel cost + ($5 × (distance - 5))
- Premium fuel delivery: no additional service charge, pay only fuel cost difference
- Diesel fuel delivery: same pricing structure as gasoline
WHAT_IS_INCLUDED: 2-3 gallons emergency fuel supply, fuel system priming if needed, basic fuel system check""",

        "winch_recovery_service.txt": """SERVICE: Winch Out Recovery Service
BASE_PRICE: 285
DESCRIPTION: Professional vehicle recovery service for vehicles stuck in mud, snow, sand, or off pavement using heavy-duty winch equipment and recovery techniques.
REQUIREMENTS: Vehicle stuck or stranded, safe access for recovery vehicle, recovery distance measured from pavement
TIME: 30-120 minutes depending on conditions and distance
PRICING_RULES:
- Fixed base fee: $285 for vehicles up to 10 feet from pavement
- Additional distance fee: $100 per each additional 10-foot increment (or fraction thereof)
- Total price formula: $285 + ($100 × number of additional 10-foot increments beyond first 10 feet)
- Distance measurement: from edge of pavement to vehicle location
- Difficult terrain surcharge: additional $150 for extreme conditions
WHAT_IS_INCLUDED: Professional recovery assessment, winch setup, vehicle extraction, basic damage inspection, cleanup of recovery area""",

        "mobile_mechanic_service.txt": """SERVICE: Mobile Mechanic Diagnostic Assessment
BASE_PRICE: 150
DESCRIPTION: Comprehensive on-site automotive diagnostic and assessment service by certified mobile mechanic with professional diagnostic equipment.
REQUIREMENTS: Vehicle with mechanical issues, owner present, access to vehicle systems
TIME: 30-90 minutes for complete assessment
PRICING_RULES:
- Daytime service (7:00 AM - 7:00 PM): $150
- Nighttime service (7:00 PM - 7:00 AM): $300
- Complex diagnostic assessment: additional $50 for electrical or computer system issues
- Multi-system diagnosis: additional $75 for comprehensive vehicle inspection
- Emergency diagnostic: standard time-based pricing applies
WHAT_IS_INCLUDED: Complete diagnostic assessment, computer system scan, written diagnostic report, repair cost estimate, maintenance recommendations""",

        "emergency_roadside_service.txt": """SERVICE: Emergency Roadside Assistance
BASE_PRICE: 125
DESCRIPTION: Priority emergency roadside assistance for urgent situations including highway breakdowns, accident recovery, and high-priority service calls.
REQUIREMENTS: Emergency situation, safe location or traffic control, immediate response needed
TIME: 15-45 minutes priority response
PRICING_RULES:
- Emergency service base fee: $125
- Highway emergency surcharge: additional $75 for interstate/freeway service
- Accident scene service: additional $100 for traffic-involved incidents
- Priority dispatch: guaranteed 30-minute response time
- Standard services at emergency rates: towing, battery, tire, lockout pricing applies
WHAT_IS_INCLUDED: Priority dispatch, emergency response, traffic safety measures, coordination with emergency services if needed""",

        "heavy_duty_towing.txt": """SERVICE: Heavy Duty Towing Service
BASE_PRICE: 350
DESCRIPTION: Specialized heavy duty towing service for large vehicles, commercial trucks, RVs, and equipment using heavy duty tow trucks and specialized equipment.
REQUIREMENTS: Heavy duty vehicle or equipment, specialized towing equipment needed, clear access for heavy duty tow truck
TIME: 45-120 minutes depending on vehicle size and conditions
PRICING_RULES:
- Heavy duty hook fee: $350 base fee
- Commercial vehicle surcharge: additional $100 for commercial trucks
- Oversized vehicle fee: additional $150 for vehicles over 26,000 lbs
- Heavy duty mileage rate: $15 per mile
- Total cost: Heavy Duty Hook Fee + Surcharges + (Mileage Rate × Distance)
- Specialized equipment fee: additional charges for rotator or heavy wrecker use
WHAT_IS_INCLUDED: Heavy duty vehicle hookup, specialized equipment usage, safe transport, professional heavy duty operators""",

        "motorcycle_towing.txt": """SERVICE: Motorcycle Towing Service
BASE_PRICE: 125
DESCRIPTION: Specialized motorcycle towing service using motorcycle-specific equipment and trailers for safe transport without damage.
REQUIREMENTS: Motorcycle or scooter, accessible location for motorcycle trailer, steering lock accessible
TIME: 20-40 minutes
PRICING_RULES:
- Motorcycle hook fee: $125
- Sport bike surcharge: additional $25 for sport bikes with fairings
- Mileage rate: $6 per mile
- Total cost: Motorcycle Hook Fee + Surcharges + (Mileage Rate × Distance)
- Multiple motorcycle discount: 10% off each additional motorcycle
WHAT_IS_INCLUDED: Motorcycle-specific loading equipment, secure tie-down, damage-free transport, motorcycle trailer usage"""
    }
    
    # Write all service documents
    for filename, content in service_docs.items():
        file_path = services_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created: {filename}")
    
    print(f"\n✅ Created {len(service_docs)} service documents")
    return len(service_docs)

async def main():
    """Main function to create all service documents"""
    
    print("📝 CREATING ALL SERVICE DOCUMENTS")
    print("=" * 50)
    print("🎯 Target: Complete roadside assistance service catalog")
    print("📁 Output: services_docs/ directory")
    print("=" * 50)
    
    # Create all documents
    doc_count = create_all_service_documents()
    
    print(f"\n🎉 SUCCESS! Created {doc_count} service documents")
    print("\n📋 Services now available:")
    print("   🚗 Professional Towing Service")
    print("   🔋 Jump Start Service") 
    print("   🛞 Tire Change Service")
    print("   🔐 Lockout Service")
    print("   ⛽ Fuel Delivery Service")
    print("   🪝 Winch Recovery Service")
    print("   🔧 Mobile Mechanic Service")
    print("   🚨 Emergency Roadside Service")
    print("   🚛 Heavy Duty Towing Service")
    print("   🏍️ Motorcycle Towing Service")
    
    print("\n💡 NEXT STEPS:")
    print("   1. Index the documents: python enhanced_kb_indexer.py")
    print("   2. Test the system: python test_rag.py")
    print("   3. Start voice AI: python main.py start")

if __name__ == "__main__":
    asyncio.run(main())