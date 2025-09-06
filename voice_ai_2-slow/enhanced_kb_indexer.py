# enhanced_kb_indexer.py - SIMPLIFIED FOR ALL SERVICES - FIXED SYNTAX
"""
Simplified Knowledge Base Indexer for ALL roadside services
No over-engineering - one clean document per service
"""
import asyncio
import logging
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from simple_rag_v2 import simplified_rag
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplifiedKnowledgeIndexer:
    """Simplified indexer for ALL roadside services"""
    
    def __init__(self):
        self.documents = []
        
    def parse_service_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse any service file into structured data"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            service_data = {
                "service_name": "",
                "base_price": "",
                "description": "",
                "requirements": "",
                "time": "",
                "pricing_rules": [],
                "raw_content": content
            }
            
            lines = content.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Parse structured sections
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
                elif current_section == "pricing_rules" and line and not line.startswith(("WHAT_IS_INCLUDED:", "ADDITIONAL_NOTES:")):
                    # Continue collecting pricing rules
                    service_data["pricing_rules"].append(line.strip())
            
            return service_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing {file_path.name}: {e}")
            return {}
    
    def classify_service_category(self, service_name: str) -> str:
        """Simple service categorization for ALL services"""
        service_lower = service_name.lower()
        
        # Map all possible services to categories
        if any(word in service_lower for word in ["towing", "tow", "transport", "flatbed", "wrecker"]):
            return "towing"
        elif any(word in service_lower for word in ["jump", "battery", "jumpstart", "boost"]):
            return "battery"
        elif any(word in service_lower for word in ["tire", "flat", "puncture", "spare"]):
            return "tire"
        elif any(word in service_lower for word in ["lockout", "locked", "keys", "unlock"]):
            return "lockout"
        elif any(word in service_lower for word in ["fuel", "gas", "gasoline", "diesel", "delivery"]):
            return "fuel"
        elif any(word in service_lower for word in ["winch", "recovery", "stuck", "off-road"]):
            return "recovery"
        elif any(word in service_lower for word in ["mechanic", "diagnostic", "repair", "inspection"]):
            return "mechanic"
        else:
            return "general"
    
    def create_single_service_document(self, service_data: Dict[str, Any], file_name: str) -> Dict[str, Any]:
        """Create ONE optimized document per service - no over-engineering"""
        
        if not service_data.get("service_name"):
            # Handle unstructured files
            return self._handle_unstructured_file(service_data, file_name)
        
        service_name = service_data["service_name"]
        base_price = service_data.get("base_price", "")
        description = service_data.get("description", "")
        pricing_rules = service_data.get("pricing_rules", [])
        time_info = service_data.get("time", "")
        requirements = service_data.get("requirements", "")
        
        # Build comprehensive service text
        text_parts = []
        
        # Service name and category
        category = self.classify_service_category(service_name)
        text_parts.append(f"{service_name}")
        
        # Pricing information (most important for queries)
        if base_price:
            if base_price.isdigit():
                text_parts.append(f"Base price: ${base_price}")
            else:
                text_parts.append(f"Pricing: {base_price}")
        
        # Description
        if description:
            text_parts.append(description)
        
        # Detailed pricing rules
        if pricing_rules:
            pricing_text = ". ".join(pricing_rules)
            text_parts.append(f"Pricing details: {pricing_text}")
        
        # Time and requirements
        if time_info:
            text_parts.append(f"Service time: {time_info}")
        
        if requirements:
            text_parts.append(f"Requirements: {requirements}")
        
        # Create final document text
        document_text = ". ".join(text_parts)
        
        return {
            "id": f"{file_name}_service",
            "text": document_text,
            "metadata": {
                "service_name": service_name,
                "category": category,
                "base_price": base_price,
                "source": "services_docs",
                "file": file_name,
                "type": "service"
            }
        }
    
    def _handle_unstructured_file(self, service_data: Dict[str, Any], file_name: str) -> Dict[str, Any]:
        """Handle unstructured files (like technical docs)"""
        
        content = service_data.get("raw_content", "")
        if not content or len(content.strip()) < 50:
            return None
        
        # Try to extract service info from content
        lines = content.split('\n')
        title_line = lines[0].strip() if lines else file_name
        
        # Determine category from filename or content
        category = self.classify_service_category(f"{file_name} {content}")
        
        return {
            "id": f"{file_name}_doc",
            "text": content,
            "metadata": {
                "service_name": title_line,
                "category": category,
                "source": "technical_docs",
                "file": file_name,
                "type": "documentation"
            }
        }
    
    def process_all_service_files(self) -> List[Dict[str, Any]]:
        """Process ALL service files in both directories"""
        
        documents = []
        
        # Process services_docs directory
        services_docs_path = Path("services_docs")
        if services_docs_path.exists():
            logger.info("📁 Processing services_docs directory...")
            
            for file_path in services_docs_path.glob("*.txt"):
                try:
                    service_data = self.parse_service_file(file_path)
                    if service_data:
                        doc = self.create_single_service_document(service_data, file_path.stem)
                        if doc:
                            documents.append(doc)
                            logger.info(f"✅ Processed: {service_data.get('service_name', file_path.name)}")
                
                except Exception as e:
                    logger.error(f"❌ Error processing {file_path.name}: {e}")
        
        # Process technical_docs directory
        technical_docs_path = Path("technical_docs")
        if technical_docs_path.exists():
            logger.info("📁 Processing technical_docs directory...")
            
            for file_path in technical_docs_path.glob("*.txt"):
                try:
                    service_data = {"raw_content": file_path.read_text(encoding='utf-8')}
                    doc = self._handle_unstructured_file(service_data, file_path.stem)
                    if doc:
                        documents.append(doc)
                        logger.info(f"✅ Processed technical doc: {file_path.name}")
                
                except Exception as e:
                    logger.error(f"❌ Error processing {file_path.name}: {e}")
        
        self.documents = documents
        logger.info(f"📊 Total documents created: {len(documents)}")
        return documents
    
    async def index_all_services(self) -> bool:
        """Index ALL services to Qdrant"""
        try:
            logger.info("🚀 Starting comprehensive service indexing...")
            start_time = time.time()
            
            # Process all service files
            documents = self.process_all_service_files()
            
            if not documents:
                logger.error("❌ No documents to index")
                return False
            
            # Initialize RAG system
            logger.info("🔧 Initializing RAG system...")
            rag_success = await simplified_rag.initialize()
            if not rag_success:
                logger.error("❌ RAG system initialization failed")
                return False
            
            # Index all documents
            logger.info(f"📤 Indexing {len(documents)} documents...")
            index_success = await simplified_rag.add_documents(documents)
            
            if index_success:
                elapsed = time.time() - start_time
                logger.info(f"✅ ALL services indexed successfully in {elapsed:.1f}s")
                
                # Test the indexing
                await self.test_all_services()
                
                return True
            else:
                logger.error("❌ Document indexing failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Indexing error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def test_all_services(self):
        """Test indexing for ALL service types"""
        logger.info("\n🧪 Testing ALL service types...")
        
        # Test queries for all service categories
        test_queries = [
            ("towing cost", "Should return towing pricing"),
            ("battery service price", "Should return battery pricing"),
            ("tire change cost", "Should return tire pricing"),
            ("lockout service", "Should return lockout pricing"),
            ("fuel delivery", "Should return fuel pricing"),
            ("winch out", "Should return recovery pricing"),
            ("mobile mechanic", "Should return mechanic pricing"),
            ("heavy duty towing", "Should return heavy duty info"),
            ("emergency service", "Should return emergency info"),
            ("roadside assistance", "Should return general info")
        ]
        
        for query, description in test_queries:
            try:
                context = await simplified_rag.retrieve_context(query, max_results=1)
                if context and len(context.strip()) > 10:
                    logger.info(f"✅ '{query}': {context[:80]}...")
                else:
                    logger.warning(f"⚠️ '{query}': No relevant content found")
            except Exception as e:
                logger.error(f"❌ Test query '{query}' failed: {e}")
    
    def get_indexing_summary(self) -> Dict[str, Any]:
        """Get comprehensive indexing summary"""
        
        categories = {}
        service_count = 0
        tech_count = 0
        
        for doc in self.documents:
            metadata = doc.get("metadata", {})
            category = metadata.get("category", "unknown")
            source = metadata.get("source", "unknown")
            
            categories[category] = categories.get(category, 0) + 1
            
            if source == "services_docs":
                service_count += 1
            elif source == "technical_docs":
                tech_count += 1
        
        return {
            "total_documents": len(self.documents),
            "service_documents": service_count,
            "technical_documents": tech_count,
            "categories": categories,
            "status": "completed" if self.documents else "no_documents"
        }

async def main():
    """Main indexing function for ALL services"""
    print("🚀 SIMPLIFIED KNOWLEDGE BASE INDEXER FOR ALL SERVICES")
    print("=" * 60)
    print("🎯 Target: All roadside assistance services")
    print("📁 Sources: services_docs/ + technical_docs/")
    print("💾 Destination: Qdrant vector database")
    print("=" * 60)
    
    try:
        indexer = SimplifiedKnowledgeIndexer()
        
        # Confirm indexing
        response = input("\n⚠️ This will replace your current knowledge base. Continue? [y/N]: ")
        if response.lower() != 'y':
            print("❌ Indexing cancelled")
            return
        
        # Index all services
        success = await indexer.index_all_services()
        
        # Get summary
        summary = indexer.get_indexing_summary()
        
        print("\n" + "=" * 60)
        print("📊 INDEXING SUMMARY")
        print("=" * 60)
        print(f"Total documents: {summary['total_documents']}")
        print(f"Service documents: {summary['service_documents']}")
        print(f"Technical documents: {summary['technical_documents']}")
        print("\nService categories:")
        for category, count in summary['categories'].items():
            print(f"  {category}: {count}")
        
        if success:
            print("\n🎉 ALL SERVICES INDEXING COMPLETED!")
            print("\n✅ Your voice AI now has complete knowledge of:")
            print("   🚗 Towing services with accurate pricing")
            print("   🔋 Battery/jumpstart services")
            print("   🛞 Tire change services")
            print("   🔐 Lockout services")
            print("   ⛽ Fuel delivery services")
            print("   🪝 Winch/recovery services")
            print("   🔧 Mobile mechanic services")
            print("   📚 Technical documentation")
            
            print("\n💡 NEXT STEPS:")
            print("   1. Test: python test_rag.py")
            print("   2. Start voice AI: python main.py start")
            print("   3. Make test call to verify ALL services work correctly")
        else:
            print("\n❌ INDEXING FAILED")
            print("   Check logs above for details")
            
    except KeyboardInterrupt:
        print("\n🛑 Indexing cancelled by user")
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())