# enhanced_kb_indexer.py - COMPREHENSIVE KNOWLEDGE BASE INDEXER
"""
Enhanced Knowledge Base Indexer for Voice AI Agent
Indexes services_docs/ and technical_docs/ for optimal voice AI performance
"""
import asyncio
import logging
import hashlib
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from simple_rag_v2 import simplified_rag
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedKnowledgeIndexer:
    """Enhanced indexer for voice AI knowledge base with service-specific optimization"""
    
    def __init__(self):
        self.documents = []
        self.service_categories = {
            "towing": ["towing", "flatbed", "wheel_lift", "heavy_duty", "light_duty", "medium_duty"],
            "battery": ["jumpstart", "battery", "change_car_battery"],
            "tire": ["tire", "flat_tire", "tire_change"],
            "lockout": ["lockout", "car_lockout"],
            "fuel": ["fuel"],
            "recovery": ["recovery", "winch", "off_road"],
            "emergency": ["emergency", "accident"]
        }
    
    def parse_service_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse structured service file into searchable components"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            service_data = {
                "service_name": "",
                "base_price": "",
                "description": "",
                "requirements": "",
                "time": "",
                "pricing_rules": []
            }
            
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith("SERVICE:"):
                    service_data["service_name"] = line.replace("SERVICE:", "").strip()
                elif line.startswith("BASE_PRICE:"):
                    service_data["base_price"] = line.replace("BASE_PRICE:", "").strip()
                elif line.startswith("DESCRIPTION:"):
                    service_data["description"] = line.replace("DESCRIPTION:", "").strip()
                elif line.startswith("REQUIREMENTS:"):
                    service_data["requirements"] = line.replace("REQUIREMENTS:", "").strip()
                elif line.startswith("TIME:"):
                    service_data["time"] = line.replace("TIME:", "").strip()
                elif line.startswith("PRICING_RULES:"):
                    current_section = "pricing_rules"
                elif current_section == "pricing_rules" and line.startswith("-"):
                    service_data["pricing_rules"].append(line[1:].strip())
            
            return service_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing {file_path.name}: {e}")
            return {}
    
    def create_service_documents(self, service_data: Dict[str, Any], file_name: str) -> List[Dict[str, Any]]:
        """Create multiple searchable documents from service data"""
        if not service_data.get("service_name"):
            return []
        
        documents = []
        service_name = service_data["service_name"]
        category = self.classify_service_category(service_name)
        
        # 1. MAIN SERVICE DOCUMENT (Primary search)
        main_text = f"{service_name}: {service_data.get('description', '')}. "
        if service_data.get("base_price"):
            main_text += f"Base price is ${service_data['base_price']}. "
        if service_data.get("time"):
            main_text += f"Service time: {service_data['time']}. "
        if service_data.get("requirements"):
            main_text += f"Requirements: {service_data['requirements']}."
        
        documents.append({
            "id": f"{file_name}_main",
            "text": main_text,
            "metadata": {
                "type": "service_main",
                "service_name": service_name,
                "category": category,
                "base_price": service_data.get("base_price", ""),
                "source": "services_docs",
                "file": file_name
            }
        })
        
        # 2. PRICING DOCUMENT (For cost inquiries)
        if service_data.get("base_price"):
            pricing_text = f"{service_name} costs ${service_data['base_price']} base price. "
            if service_data.get("pricing_rules"):
                pricing_text += "Additional charges: " + ". ".join(service_data["pricing_rules"])
            
            documents.append({
                "id": f"{file_name}_pricing",
                "text": pricing_text,
                "metadata": {
                    "type": "pricing",
                    "service_name": service_name,
                    "category": category,
                    "base_price": service_data.get("base_price", ""),
                    "source": "services_docs",
                    "file": file_name
                }
            })
        
        # 3. CATEGORY DOCUMENT (For category-based searches)
        category_text = f"{category.title()} service: {service_name}. {service_data.get('description', '')}. "
        if service_data.get("base_price"):
            category_text += f"Starting at ${service_data['base_price']}."
        
        documents.append({
            "id": f"{file_name}_category",
            "text": category_text,
            "metadata": {
                "type": "category",
                "service_name": service_name,
                "category": category,
                "base_price": service_data.get("base_price", ""),
                "source": "services_docs",
                "file": file_name
            }
        })
        
        # 4. VEHICLE-SPECIFIC DOCUMENTS (For vehicle type matching)
        vehicle_keywords = self.extract_vehicle_keywords(service_name)
        if vehicle_keywords:
            for vehicle_type in vehicle_keywords:
                vehicle_text = f"{vehicle_type} {service_name}: {service_data.get('description', '')}. "
                if service_data.get("base_price"):
                    vehicle_text += f"Price: ${service_data['base_price']}."
                
                documents.append({
                    "id": f"{file_name}_vehicle_{vehicle_type}",
                    "text": vehicle_text,
                    "metadata": {
                        "type": "vehicle_specific",
                        "service_name": service_name,
                        "category": category,
                        "vehicle_type": vehicle_type,
                        "base_price": service_data.get("base_price", ""),
                        "source": "services_docs",
                        "file": file_name
                    }
                })
        
        return documents
    
    def classify_service_category(self, service_name: str) -> str:
        """Classify service into main categories for agent routing"""
        service_lower = service_name.lower()
        
        for category, keywords in self.service_categories.items():
            if any(keyword in service_lower for keyword in keywords):
                return category
        
        return "general"
    
    def extract_vehicle_keywords(self, service_name: str) -> List[str]:
        """Extract vehicle-specific keywords from service name"""
        service_lower = service_name.lower()
        vehicle_types = []
        
        vehicle_mappings = {
            "18 wheeler": ["18_wheeler", "semi", "truck"],
            "semi": ["semi", "truck"],
            "heavy duty": ["heavy_duty", "truck"],
            "medium duty": ["medium_duty", "truck"],
            "light duty": ["light_duty", "car"],
            "motorcycle": ["motorcycle"],
            "rv": ["rv", "motorhome"],
            "motorhome": ["motorhome", "rv"],
            "bus": ["bus"],
            "limo": ["limo", "limousine"],
            "luxury": ["luxury", "exotic"],
            "construction": ["construction", "equipment"],
            "commercial": ["commercial", "fleet"]
        }
        
        for key, types in vehicle_mappings.items():
            if key in service_lower:
                vehicle_types.extend(types)
        
        return list(set(vehicle_types))
    
    def process_technical_docs(self) -> List[Dict[str, Any]]:
        """Process technical documentation files"""
        tech_docs_path = Path("technical_docs")
        documents = []
        
        if not tech_docs_path.exists():
            logger.warning("⚠️ technical_docs/ directory not found")
            return []
        
        for file_path in tech_docs_path.glob("*.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                
                if not content:
                    continue
                
                # Split into sections for better searchability
                sections = content.split('\n\n')
                
                for i, section in enumerate(sections):
                    if len(section.strip()) < 50:  # Skip very short sections
                        continue
                    
                    doc_id = f"tech_{file_path.stem}_section_{i}"
                    
                    documents.append({
                        "id": doc_id,
                        "text": section.strip(),
                        "metadata": {
                            "type": "technical",
                            "source": "technical_docs",
                            "file": file_path.name,
                            "section": i
                        }
                    })
                
                logger.info(f"✅ Processed technical doc: {file_path.name} ({len(sections)} sections)")
                
            except Exception as e:
                logger.error(f"❌ Error processing {file_path.name}: {e}")
        
        return documents
    
    def process_services_docs(self) -> List[Dict[str, Any]]:
        """Process all service documentation files"""
        services_docs_path = Path("services_docs")
        documents = []
        
        if not services_docs_path.exists():
            logger.warning("⚠️ services_docs/ directory not found")
            return []
        
        for file_path in services_docs_path.glob("*.txt"):
            try:
                service_data = self.parse_service_file(file_path)
                if service_data:
                    service_docs = self.create_service_documents(service_data, file_path.stem)
                    documents.extend(service_docs)
                    logger.info(f"✅ Processed service: {service_data.get('service_name', file_path.name)} ({len(service_docs)} docs)")
                
            except Exception as e:
                logger.error(f"❌ Error processing {file_path.name}: {e}")
        
        return documents
    
    async def index_knowledge_base(self) -> bool:
        """Index complete knowledge base to Qdrant"""
        try:
            logger.info("🚀 Starting enhanced knowledge base indexing...")
            start_time = time.time()
            
            # Process services documentation
            logger.info("📋 Processing services documentation...")
            service_docs = self.process_services_docs()
            logger.info(f"✅ Services: {len(service_docs)} documents created")
            
            # Process technical documentation
            logger.info("📘 Processing technical documentation...")
            tech_docs = self.process_technical_docs()
            logger.info(f"✅ Technical: {len(tech_docs)} documents created")
            
            # Combine all documents
            all_documents = service_docs + tech_docs
            self.documents = all_documents
            
            if not all_documents:
                logger.error("❌ No documents to index")
                return False
            
            logger.info(f"📊 Total documents to index: {len(all_documents)}")
            
            # Initialize RAG system
            logger.info("🔧 Initializing RAG system...")
            rag_success = await simplified_rag.initialize()
            if not rag_success:
                logger.error("❌ RAG system initialization failed")
                return False
            
            # Index documents
            logger.info("📤 Indexing documents to Qdrant...")
            index_success = await simplified_rag.add_documents(all_documents)
            
            if index_success:
                elapsed = time.time() - start_time
                logger.info(f"✅ Knowledge base indexed successfully in {elapsed:.1f}s")
                
                # Test the knowledge base
                await self.test_knowledge_base()
                
                return True
            else:
                logger.error("❌ Document indexing failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Indexing error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def test_knowledge_base(self):
        """Test the indexed knowledge base with voice AI scenarios"""
        logger.info("\n🧪 Testing knowledge base with voice AI scenarios...")
        
        test_queries = [
            ("towing cost", "pricing"),
            ("battery service price", "pricing"),
            ("tire change", "service"),
            ("locked out of car", "service"),
            ("fuel delivery", "service"),
            ("heavy duty truck towing", "vehicle_specific"),
            ("motorcycle towing", "vehicle_specific"),
            ("emergency roadside assistance", "emergency"),
            ("BMW towing", "luxury"),
            ("semi truck help", "commercial")
        ]
        
        for query, expected_type in test_queries:
            try:
                context = await simplified_rag.retrieve_context(query, max_results=2)
                if context and len(context.strip()) > 10:
                    logger.info(f"✅ '{query}': Found relevant content")
                    logger.debug(f"   Context: {context[:80]}...")
                else:
                    logger.warning(f"⚠️ '{query}': No relevant content found")
            except Exception as e:
                logger.error(f"❌ Test query '{query}' failed: {e}")
    
    def get_indexing_summary(self) -> Dict[str, Any]:
        """Get comprehensive indexing summary"""
        service_count = len([d for d in self.documents if d["metadata"]["source"] == "services_docs"])
        tech_count = len([d for d in self.documents if d["metadata"]["source"] == "technical_docs"])
        
        categories = {}
        for doc in self.documents:
            if "category" in doc["metadata"]:
                cat = doc["metadata"]["category"]
                categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_documents": len(self.documents),
            "service_documents": service_count,
            "technical_documents": tech_count,
            "categories": categories,
            "document_types": {
                "service_main": len([d for d in self.documents if d["metadata"]["type"] == "service_main"]),
                "pricing": len([d for d in self.documents if d["metadata"]["type"] == "pricing"]),
                "category": len([d for d in self.documents if d["metadata"]["type"] == "category"]),
                "vehicle_specific": len([d for d in self.documents if d["metadata"]["type"] == "vehicle_specific"]),
                "technical": len([d for d in self.documents if d["metadata"]["type"] == "technical"])
            }
        }

async def main():
    """Main indexing function"""
    print("🚀 ENHANCED VOICE AI KNOWLEDGE BASE INDEXER")
    print("=" * 60)
    print("🎯 Target: Voice AI optimized knowledge base")
    print("📁 Sources: services_docs/ + technical_docs/")
    print("💾 Destination: Qdrant vector database")
    print("=" * 60)
    
    try:
        indexer = EnhancedKnowledgeIndexer()
        
        # Confirm indexing
        response = input("\n⚠️ This will replace your current knowledge base. Continue? [y/N]: ")
        if response.lower() != 'y':
            print("❌ Indexing cancelled")
            return
        
        # Index knowledge base
        success = await indexer.index_knowledge_base()
        
        # Get summary
        summary = indexer.get_indexing_summary()
        
        print("\n" + "=" * 60)
        print("📊 INDEXING SUMMARY")
        print("=" * 60)
        print(f"Total documents: {summary['total_documents']}")
        print(f"Service documents: {summary['service_documents']}")
        print(f"Technical documents: {summary['technical_documents']}")
        print("\nDocument types:")
        for doc_type, count in summary['document_types'].items():
            print(f"  {doc_type}: {count}")
        
        print("\nService categories:")
        for category, count in summary['categories'].items():
            print(f"  {category}: {count}")
        
        if success:
            print("\n🎉 KNOWLEDGE BASE INDEXING COMPLETED!")
            print("\n✅ Your voice AI agent now has:")
            print("   📋 Complete service catalog with pricing")
            print("   🎯 Optimized search for voice queries")
            print("   🚗 Vehicle-specific service matching")
            print("   💰 Precise pricing information")
            print("   📞 Ready for customer calls!")
            
            print("\n💡 NEXT STEPS:")
            print("   1. Test your agent: python main.py")
            print("   2. Make a test call to your number")
            print("   3. Ask about services: 'How much does towing cost?'")
            print("   4. Test different scenarios: battery, tire, lockout, etc.")
        else:
            print("\n❌ INDEXING FAILED")
            print("   Check logs above for details")
            
    except KeyboardInterrupt:
        print("\n🛑 Indexing cancelled by user")
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())