# excel_to_qdrant_indexer.py - FIXED VERSION
"""
FIXED: Excel to Qdrant Indexer for Voice AI Knowledge Base
Fixes the document storage issue
"""
import asyncio
import logging
import sys
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import argparse

# Import your existing systems
from simple_rag_v2 import simplified_rag
from config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixedExcelToQdrantIndexer:
    """FIXED: Index Excel files to Qdrant for voice AI knowledge base"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.documents = []  # This will store ALL documents
        self.processed_files = []
        
    def find_excel_files(self) -> List[Path]:
        """Find all Excel files in the data directory"""
        excel_extensions = ['.xlsx', '.xls', '.xlsm']
        excel_files = []
        
        if not self.data_dir.exists():
            logger.error(f"❌ Data directory not found: {self.data_dir}")
            return []
        
        for ext in excel_extensions:
            excel_files.extend(self.data_dir.glob(f"*{ext}"))
        
        logger.info(f"📁 Found {len(excel_files)} Excel files in {self.data_dir}")
        for file in excel_files:
            logger.info(f"   📄 {file.name}")
        
        return excel_files
    
    def read_excel_file(self, excel_path: Path) -> Dict[str, pd.DataFrame]:
        """Read all sheets from an Excel file"""
        try:
            logger.info(f"📖 Reading Excel file: {excel_path.name}")
            
            # Read all sheets
            excel_data = pd.read_excel(
                excel_path,
                sheet_name=None,  # Read all sheets
                engine='openpyxl'
            )
            
            logger.info(f"✅ Successfully read {len(excel_data)} sheets from {excel_path.name}")
            for sheet_name, df in excel_data.items():
                logger.info(f"   📋 {sheet_name}: {len(df)} rows, {len(df.columns)} columns")
            
            return excel_data
            
        except Exception as e:
            logger.error(f"❌ Failed to read Excel file {excel_path.name}: {e}")
            return {}
    
    def process_services_sheet(self, df: pd.DataFrame, file_name: str) -> List[Dict[str, Any]]:
        """Process Services/Roadside sheet into searchable documents"""
        documents = []
        
        logger.info("🔧 Processing Services sheet...")
        
        for idx, row in df.iterrows():
            try:
                # Handle different possible column names
                service_cols = ['Service Type', 'Service', 'Service Name', 'Type']
                name_cols = ['Service Name', 'Name', 'Service', 'Description']
                cost_cols = ['Base Cost', 'Cost', 'Price', 'Fee', 'Amount']
                desc_cols = ['Description', 'Details', 'Additional Details', 'Info']
                
                # Find the actual column names
                service_type = self._find_column_value(row, service_cols)
                service_name = self._find_column_value(row, name_cols)
                cost = self._find_column_value(row, cost_cols)
                description = self._find_column_value(row, desc_cols)
                
                # Skip empty rows
                if not service_name and not service_type:
                    continue
                
                # Create comprehensive search text
                search_texts = []
                
                # Main service document
                main_parts = []
                if service_name:
                    main_parts.append(f"Service: {service_name}")
                if service_type:
                    main_parts.append(f"Type: {service_type}")
                if description:
                    main_parts.append(f"Description: {description}")
                if cost:
                    main_parts.append(f"Cost: {cost}")
                
                main_text = ". ".join(main_parts)
                if main_text:
                    search_texts.append({
                        "text": main_text,
                        "type": "service_info"
                    })
                
                # Pricing-specific document
                if cost and service_name:
                    pricing_text = f"{service_name} costs {cost}. {description}" if description else f"{service_name} costs {cost}"
                    search_texts.append({
                        "text": pricing_text,
                        "type": "pricing"
                    })
                
                # Service type document
                if service_type and service_name:
                    type_text = f"{service_type}: {service_name}"
                    if cost:
                        type_text += f" - {cost}"
                    search_texts.append({
                        "text": type_text,
                        "type": "service_category"
                    })
                
                # Create documents
                for search_item in search_texts:
                    doc_id = hashlib.md5(f"{file_name}_{idx}_{search_item['type']}".encode()).hexdigest()
                    
                    document = {
                        "id": doc_id,
                        "text": search_item["text"],
                        "metadata": {
                            "source_file": file_name,
                            "sheet": "Services",
                            "row": idx,
                            "service_type": service_type or "general",
                            "service_name": service_name or "unnamed",
                            "cost": cost or "not specified",
                            "document_type": search_item["type"],
                            "indexed_at": time.time()
                        }
                    }
                    documents.append(document)
                
                logger.debug(f"   ✅ Processed row {idx}: {service_name or service_type}")
                
            except Exception as e:
                logger.warning(f"⚠️ Error processing row {idx}: {e}")
                continue
        
        logger.info(f"✅ Services sheet: {len(documents)} documents created")
        return documents
    
    def process_generic_sheet(self, df: pd.DataFrame, sheet_name: str, file_name: str) -> List[Dict[str, Any]]:
        """Process any generic sheet into searchable documents"""
        documents = []
        
        logger.info(f"📊 Processing generic sheet: {sheet_name}")
        
        # Get all columns
        columns = df.columns.tolist()
        
        for idx, row in df.iterrows():
            try:
                # Skip completely empty rows
                if row.isna().all():
                    continue
                
                # Create text from all non-empty columns
                text_parts = []
                metadata = {
                    "source_file": file_name,
                    "sheet": sheet_name,
                    "row": idx,
                    "indexed_at": time.time()
                }
                
                for col in columns:
                    value = row[col]
                    if pd.notna(value) and str(value).strip():
                        clean_value = str(value).strip()
                        text_parts.append(f"{col}: {clean_value}")
                        # Also store in metadata
                        metadata[col.lower().replace(' ', '_')] = clean_value
                
                if text_parts:
                    doc_text = ". ".join(text_parts)
                    doc_id = hashlib.md5(f"{file_name}_{sheet_name}_{idx}".encode()).hexdigest()
                    
                    document = {
                        "id": doc_id,
                        "text": doc_text,
                        "metadata": metadata
                    }
                    documents.append(document)
                
            except Exception as e:
                logger.warning(f"⚠️ Error processing row {idx} in {sheet_name}: {e}")
                continue
        
        logger.info(f"✅ {sheet_name} sheet: {len(documents)} documents created")
        return documents
    
    def _find_column_value(self, row: pd.Series, possible_columns: List[str]) -> Optional[str]:
        """Find value from row using possible column names"""
        for col in possible_columns:
            if col in row.index and pd.notna(row[col]):
                return str(row[col]).strip()
        return None
    
    def process_excel_file(self, excel_path: Path) -> List[Dict[str, Any]]:
        """FIXED: Process entire Excel file into documents and STORE them"""
        file_documents = []
        
        excel_data = self.read_excel_file(excel_path)
        if not excel_data:
            return []
        
        for sheet_name, df in excel_data.items():
            logger.info(f"\n📊 Processing sheet: {sheet_name}")
            
            # Determine sheet type and process accordingly
            if any(keyword in sheet_name.lower() for keyword in ['service', 'roadside', 'assist']):
                documents = self.process_services_sheet(df, excel_path.name)
            else:
                documents = self.process_generic_sheet(df, sheet_name, excel_path.name)
            
            file_documents.extend(documents)
        
        self.processed_files.append(excel_path.name)
        
        # CRITICAL FIX: Store documents in self.documents
        self.documents.extend(file_documents)
        
        logger.info(f"✅ File processed: {excel_path.name} - {len(file_documents)} documents")
        logger.info(f"📊 Total documents stored: {len(self.documents)}")
        
        return file_documents
    
    def process_all_excel_files(self) -> List[Dict[str, Any]]:
        """Process all Excel files in data directory"""
        excel_files = self.find_excel_files()
        
        if not excel_files:
            logger.error("❌ No Excel files found in data directory")
            return []
        
        # Clear documents list
        self.documents = []
        
        for excel_file in excel_files:
            logger.info(f"\n🔄 Processing file: {excel_file.name}")
            file_docs = self.process_excel_file(excel_file)
            logger.info(f"✅ {excel_file.name}: {len(file_docs)} documents extracted")
        
        logger.info(f"\n📊 Total documents created: {len(self.documents)}")
        return self.documents
    
    async def index_to_qdrant(self) -> bool:
        """FIXED: Index all documents to Qdrant via simplified RAG"""
        try:
            if not self.documents:
                logger.error("❌ No documents to index. Documents list is empty.")
                logger.info(f"📊 Total documents in memory: {len(self.documents)}")
                return False
            
            logger.info(f"🚀 Starting Qdrant indexing of {len(self.documents)} documents...")
            
            # Initialize RAG system
            logger.info("🔧 Initializing Qdrant RAG system...")
            success = await simplified_rag.initialize()
            
            if not success:
                logger.error("❌ Failed to initialize RAG system")
                return False
            
            # Add documents to Qdrant
            logger.info("📤 Adding documents to Qdrant...")
            start_time = time.time()
            
            success = await simplified_rag.add_documents(self.documents)
            
            if success:
                ingest_time = time.time() - start_time
                logger.info(f"✅ Indexing completed in {ingest_time:.2f} seconds")
                
                # Test the indexing
                await self._test_indexing()
                
                return True
            else:
                logger.error("❌ Document indexing failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Indexing error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    async def _test_indexing(self):
        """Test the indexed knowledge base"""
        logger.info("\n🧪 Testing indexed knowledge base...")
        
        test_queries = [
            "service cost",
            "towing price", 
            "battery help",
            "tire service",
            "roadside assistance"
        ]
        
        for query in test_queries:
            try:
                context = await simplified_rag.retrieve_context(query, max_results=2)
                if context:
                    logger.info(f"✅ '{query}': Found relevant content")
                    logger.debug(f"   Context: {context[:100]}...")
                else:
                    logger.warning(f"⚠️ '{query}': No relevant content found")
            except Exception as e:
                logger.error(f"❌ Test query '{query}' failed: {e}")
    
    def get_indexing_summary(self) -> Dict[str, Any]:
        """Get summary of indexing process"""
        return {
            "files_processed": len(self.processed_files),
            "processed_files": self.processed_files,
            "total_documents": len(self.documents),
            "document_types": self._get_document_type_distribution(),
            "status": "completed" if self.documents else "no_documents"
        }
    
    def _get_document_type_distribution(self) -> Dict[str, int]:
        """Get distribution of document types"""
        distribution = {}
        for doc in self.documents:
            doc_type = doc["metadata"].get("document_type", "unknown")
            distribution[doc_type] = distribution.get(doc_type, 0) + 1
        return distribution

async def main():
    """Main indexing function"""
    parser = argparse.ArgumentParser(description="Index Excel files to Qdrant for Voice AI")
    parser.add_argument("--file", "-f", help="Specific Excel file to index (optional)")
    parser.add_argument("--test", "-t", action="store_true", help="Run tests after indexing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        logger.info("🚀 FIXED EXCEL TO QDRANT INDEXER")
        logger.info(f"📁 Data directory: {Path('data').absolute()}")
        logger.info(f"🎯 Target: Qdrant at {config.qdrant_url}")
        logger.info("=" * 60)
        
        # Create indexer
        indexer = FixedExcelToQdrantIndexer()
        
        # Process Excel files
        if args.file:
            logger.info(f"\n📊 Processing specific file: {args.file}")
            excel_path = Path("data") / args.file
            if excel_path.exists():
                documents = indexer.process_excel_file(excel_path)
                logger.info(f"📊 Documents created from file: {len(documents)}")
                logger.info(f"📊 Total documents in indexer: {len(indexer.documents)}")
            else:
                logger.error(f"❌ File not found: {excel_path}")
                return
        else:
            logger.info("\n📊 Processing all Excel files in data directory...")
            documents = indexer.process_all_excel_files()
        
        logger.info(f"\n📊 BEFORE INDEXING CHECK:")
        logger.info(f"   Documents to index: {len(indexer.documents)}")
        
        if not indexer.documents:
            logger.error("❌ No documents were created - check your Excel file format")
            return
        
        # Index to Qdrant
        logger.info("\n🚀 Step 2: Indexing to Qdrant...")
        success = await indexer.index_to_qdrant()
        
        # Get summary
        summary = indexer.get_indexing_summary()
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 INDEXING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Files processed: {summary['files_processed']}")
        logger.info(f"Total documents: {summary['total_documents']}")
        logger.info(f"Document types: {summary['document_types']}")
        
        if success:
            logger.info("\n🎉 INDEXING COMPLETED SUCCESSFULLY!")
            logger.info("\n✅ Your voice AI knowledge base is ready!")
            logger.info("\n💡 NEXT STEPS:")
            logger.info("   1. Start your voice AI: python main.py dev")
            logger.info("   2. Test with voice queries about your services")
            logger.info("   3. Ask about pricing, services, or any Excel content")
            
            if args.test:
                logger.info("\n🧪 Running additional tests...")
                await indexer._test_indexing()
                
        else:
            logger.error("\n❌ INDEXING FAILED!")
            logger.error("   Check Qdrant connection and try again")
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Indexing cancelled by user")
    except Exception as e:
        logger.error(f"\n❌ FATAL ERROR: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())