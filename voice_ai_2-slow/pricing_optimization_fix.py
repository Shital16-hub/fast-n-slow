# pricing_optimization_fix.py - QUICK FIX FOR PRICING QUERIES
"""
Quick fix to ensure all pricing queries return actual pricing information
"""
import asyncio
from pathlib import Path

def create_pricing_focused_documents():
    """Create additional pricing-focused documents for better retrieval"""
    
    services_dir = Path("services_docs")
    
    # Create focused pricing documents
    pricing_docs = {
        "heavy_duty_towing_pricing.txt": """SERVICE: Heavy Duty Towing Pricing
BASE_PRICE: 350
DESCRIPTION: Heavy duty towing pricing - base fee $350, commercial vehicle surcharge $100, oversized vehicle fee $150, mileage rate $15 per mile.
PRICING_RULES:
- Heavy duty hook fee: $350 base fee
- Commercial vehicle surcharge: additional $100 for commercial trucks
- Oversized vehicle fee: additional $150 for vehicles over 26,000 lbs
- Heavy duty mileage rate: $15 per mile
- Total cost: Heavy Duty Hook Fee + Surcharges + (Mileage Rate × Distance)""",

        "motorcycle_towing_pricing.txt": """SERVICE: Motorcycle Towing Pricing
BASE_PRICE: 125
DESCRIPTION: Motorcycle towing pricing - hook fee $125, sport bike surcharge $25, mileage rate $6 per mile.
PRICING_RULES:
- Motorcycle hook fee: $125
- Sport bike surcharge: additional $25 for sport bikes with fairings
- Mileage rate: $6 per mile
- Total cost: Motorcycle Hook Fee + Surcharges + (Mileage Rate × Distance)
- Multiple motorcycle discount: 10% off each additional motorcycle""",

        "dead_battery_service_pricing.txt": """SERVICE: Dead Battery Service Pricing
BASE_PRICE: 150
DESCRIPTION: Dead battery jumpstart service pricing - $150 daytime, $200 nighttime, multiple battery pricing available.
PRICING_RULES:
- Daytime service (7:00 AM - 7:00 PM): $150
- Nighttime service (7:00 PM - 7:00 AM): $200
- Multiple battery pricing: 2 batteries $229, 3 batteries $265, 4 batteries $295
- Service includes battery testing and basic electrical system check""",

        "flat_tire_service_pricing.txt": """SERVICE: Flat Tire Service Pricing
BASE_PRICE: 165
DESCRIPTION: Flat tire change service pricing - $165 daytime, $200 nighttime, additional surcharges for special tires.
PRICING_RULES:
- Daytime service (7:00 AM - 7:00 PM): $165
- Nighttime service (7:00 PM - 7:00 AM): $200
- Run-flat tire service: additional $25 surcharge
- Wheel lock removal: additional $35 if special key not available""",

        "out_of_gas_service_pricing.txt": """SERVICE: Out of Gas Service Pricing
BASE_PRICE: 199
DESCRIPTION: Emergency fuel delivery pricing - $199 base fee plus fuel cost, first 5 miles included, $5 per additional mile.
PRICING_RULES:
- Base service fee: $199 plus cost of fuel
- Distance allowance: first 5 miles included in base price
- Additional mileage: $5 per mile for distances over 5 miles
- Total price if distance over 5 miles: $199 + fuel cost + ($5 × (distance - 5))""",

        "stuck_vehicle_recovery_pricing.txt": """SERVICE: Stuck Vehicle Recovery Pricing
BASE_PRICE: 285
DESCRIPTION: Vehicle recovery pricing - $285 base fee for up to 10 feet, $100 per additional 10-foot increment, difficult terrain surcharge $150.
PRICING_RULES:
- Fixed base fee: $285 for vehicles up to 10 feet from pavement
- Additional distance fee: $100 per each additional 10-foot increment
- Total price formula: $285 + ($100 × number of additional 10-foot increments beyond first 10 feet)
- Difficult terrain surcharge: additional $150 for extreme conditions""",

        "highway_emergency_service_pricing.txt": """SERVICE: Highway Emergency Service Pricing
BASE_PRICE: 125
DESCRIPTION: Highway emergency service pricing - $125 base fee, highway surcharge $75, accident scene service $100 additional.
PRICING_RULES:
- Emergency service base fee: $125
- Highway emergency surcharge: additional $75 for interstate/freeway service
- Accident scene service: additional $100 for traffic-involved incidents
- Priority dispatch: guaranteed 30-minute response time"""
    }
    
    # Write pricing-focused documents
    for filename, content in pricing_docs.items():
        file_path = services_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Created pricing doc: {filename}")
    
    print(f"\n✅ Created {len(pricing_docs)} pricing-focused documents")
    return len(pricing_docs)

async def reindex_with_pricing_focus():
    """Re-index with pricing-focused documents"""
    
    print("📝 CREATING PRICING-FOCUSED DOCUMENTS")
    print("=" * 50)
    
    # Create pricing documents
    doc_count = create_pricing_focused_documents()
    
    print(f"\n✅ Created {doc_count} additional pricing documents")
    print("\n🔄 Now re-indexing to include pricing-focused content...")
    
    # Re-run indexer
    try:
        from enhanced_kb_indexer import SimplifiedKnowledgeIndexer
        
        indexer = SimplifiedKnowledgeIndexer()
        success = await indexer.index_all_services()
        
        if success:
            print("✅ Re-indexing completed successfully!")
            
            # Test the improvements
            print("\n🧪 Testing pricing improvements...")
            await test_pricing_queries()
            
        else:
            print("❌ Re-indexing failed")
            
    except Exception as e:
        print(f"❌ Error during re-indexing: {e}")

async def test_pricing_queries():
    """Test the specific queries that were failing"""
    
    from simple_rag_v2 import simplified_rag
    
    # Test the queries that were missing pricing
    failing_queries = [
        "heavy duty towing",
        "motorcycle towing", 
        "dead battery help",
        "flat tire service",
        "out of gas service",
        "stuck vehicle recovery",
        "highway emergency service"
    ]
    
    print("🔍 Testing previously failing queries...")
    
    improved_count = 0
    
    for query in failing_queries:
        try:
            result = await simplified_rag.retrieve_context(query, max_results=1)
            
            # Check for pricing indicators
            has_pricing = any(indicator in result.lower() for indicator in [
                '$', 'price', 'cost', 'fee', '125', '150', '165', '199', '285', '350'
            ])
            
            if has_pricing:
                print(f"✅ IMPROVED '{query}': {result[:80]}...")
                improved_count += 1
            else:
                print(f"⚠️ Still missing pricing '{query}': {result[:80]}...")
                
        except Exception as e:
            print(f"❌ Error testing '{query}': {e}")
    
    improvement_rate = (improved_count / len(failing_queries)) * 100
    print(f"\n📊 Improvement: {improved_count}/{len(failing_queries)} queries fixed ({improvement_rate:.1f}%)")
    
    return improvement_rate > 70

async def main():
    """Main optimization function"""
    
    print("🔧 PRICING OPTIMIZATION FIX")
    print("=" * 40)
    print("🎯 Goal: Improve pricing query results")
    print("💡 Method: Add pricing-focused documents")
    print("=" * 40)
    
    success = await reindex_with_pricing_focus()
    
    if success:
        print("\n🎉 PRICING OPTIMIZATION COMPLETED!")
        print("\n💡 NEXT STEPS:")
        print("   1. Run full test: python test_all_services.py")
        print("   2. Should see 85%+ success rate")
        print("   3. Start voice AI: python main.py start")
    else:
        print("\n⚠️ OPTIMIZATION HAD ISSUES")
        print("💡 Manual fallback:")
        print("   1. python enhanced_kb_indexer.py")
        print("   2. python test_all_services.py")

if __name__ == "__main__":
    asyncio.run(main())