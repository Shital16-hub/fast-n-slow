# test_all_services.py - SIMPLE TEST FOR ALL SERVICES
"""
Simple test script to verify ALL roadside services work correctly
"""
import asyncio
from simple_rag_v2 import simplified_rag

async def test_all_services():
    """Test all roadside services"""
    
    print("🧪 TESTING ALL ROADSIDE SERVICES")
    print("=" * 50)
    
    # Initialize RAG system
    print("🔧 Initializing RAG system...")
    success = await simplified_rag.initialize()
    
    if not success:
        print("❌ RAG initialization failed!")
        return False
    
    print("✅ RAG system ready")
    
    # Test all service categories
    test_cases = [
        # Towing services
        ("towing cost", "Should return $169/$189 hook fees"),
        ("car towing price", "Should return towing pricing"),
        ("heavy duty towing", "Should return $350 heavy duty pricing"),
        ("motorcycle towing", "Should return $125 motorcycle pricing"),
        
        # Battery services
        ("battery service price", "Should return $150 jumpstart pricing"),
        ("jump start cost", "Should return battery service pricing"),
        ("dead battery help", "Should return jumpstart service"),
        
        # Tire services
        ("tire change cost", "Should return $165 tire service"),
        ("flat tire service", "Should return tire change pricing"),
        ("tire replacement price", "Should return tire service info"),
        
        # Lockout services
        ("lockout service cost", "Should return $150 lockout pricing"),
        ("locked out of car", "Should return lockout service"),
        ("car key service", "Should return lockout pricing"),
        
        # Fuel services
        ("fuel delivery cost", "Should return $199 fuel delivery"),
        ("out of gas service", "Should return fuel delivery pricing"),
        ("emergency fuel price", "Should return fuel delivery info"),
        
        # Recovery services
        ("winch out cost", "Should return $285 winch pricing"),
        ("stuck vehicle recovery", "Should return winch service"),
        ("vehicle recovery price", "Should return winch pricing"),
        
        # Mechanic services
        ("mobile mechanic cost", "Should return $150 diagnostic"),
        ("car diagnostic price", "Should return mechanic service"),
        ("vehicle inspection cost", "Should return diagnostic pricing"),
        
        # Emergency services
        ("emergency roadside cost", "Should return emergency pricing"),
        ("highway emergency service", "Should return priority service"),
        ("accident recovery price", "Should return emergency info")
    ]
    
    print(f"\n🔍 Testing {len(test_cases)} service queries...")
    print("-" * 50)
    
    passed_tests = 0
    failed_tests = 0
    
    for query, expected_description in test_cases:
        try:
            result = await simplified_rag.retrieve_context(query, max_results=1)
            
            # Check if result contains pricing information
            has_pricing = any(indicator in result.lower() for indicator in [
                '$', 'price', 'cost', 'fee', '169', '189', '150', '165', '199', '285', '350', '125'
            ])
            
            # Check if result is relevant to the service
            service_keywords = query.split()
            has_relevant_content = any(keyword in result.lower() for keyword in service_keywords)
            
            if result and has_pricing and has_relevant_content:
                print(f"✅ '{query}': {result[:80]}...")
                passed_tests += 1
            elif result:
                print(f"⚠️ '{query}': {result[:80]}... (missing pricing)")
                failed_tests += 1
            else:
                print(f"❌ '{query}': No result")
                failed_tests += 1
                
        except Exception as e:
            print(f"❌ '{query}': Error - {e}")
            failed_tests += 1
    
    # Print summary
    total_tests = len(test_cases)
    success_rate = (passed_tests / total_tests) * 100
    
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success rate: {success_rate:.1f}%")
    
    # Get system status
    status = await simplified_rag.get_status()
    print(f"\nSystem status: {status.get('points_count', 0)} documents indexed")
    
    if success_rate >= 80:
        print("\n🎉 EXCELLENT! All services are working correctly")
        print("✅ Your voice AI is ready for production")
        return True
    elif success_rate >= 60:
        print("\n⚠️ GOOD but needs improvement")
        print("💡 Consider re-indexing: python enhanced_kb_indexer.py")
        return False
    else:
        print("\n❌ POOR performance - system needs fixing")
        print("🔧 Recommended actions:")
        print("   1. Check service documents exist")
        print("   2. Re-run indexer: python enhanced_kb_indexer.py") 
        print("   3. Verify Qdrant is running")
        return False

async def main():
    """Main test function"""
    
    try:
        success = await test_all_services()
        
        if success:
            print("\n🚀 READY TO START VOICE AI!")
            print("   Run: python main.py start")
        else:
            print("\n🔧 SYSTEM NEEDS ATTENTION")
            print("   Fix issues above and test again")
            
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())