"""
VF CSV to Knowledge Graph Parser
Optimized for Virtue Foundation Ghana CSV format
Enhanced with LLM extraction and validation
"""

import ast
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple
import os
from langchain_core.messages import HumanMessage, SystemMessage
from .llm_extractor import LLMExtractor
from .llm_factory import get_llm
from .entity_validator import EntityValidator
from .relationship_classifier import RelationshipClassifier

import pandas as pd

logger = logging.getLogger(__name__)


class VFCSVParser:
    """Parse VF CSV and build knowledge graph with LLM enhancement"""
    
    def __init__(self, model=None, enable_llm_extraction=False, llm_provider=None):
        provider = llm_provider or os.getenv("LLM_PROVIDER", "ollama").strip().lower()
        self.llm = get_llm(provider=provider, model=model)

        self.classifier = RelationshipClassifier(provider=provider)
        self.enable_llm_extraction = enable_llm_extraction
        if enable_llm_extraction:
            # Use OLLAMA_MODEL_EXTRACTOR for extraction only (e.g. qwen2.5:7b); else default OLLAMA_MODEL
            extractor_model = os.getenv("OLLAMA_MODEL_EXTRACTOR") or model
            self.llm_extractor = LLMExtractor(provider=provider, model=extractor_model)
            self.validator = EntityValidator()
            logger.info("LLM extraction enabled: %s", self.llm_extractor.enabled)
        else:
            self.llm_extractor = None
            self.validator = None
            logger.info("LLM extraction disabled (use enable_llm=True to enable)")
        
        logger.info("Intelligent relationship classification: %s", self.classifier.enabled)
    
    def _is_valid_capability(self, text: str) -> bool:
        """Check if text is a valid service capability (not location/number/junk)"""
        if not text or not isinstance(text, str):
            return False
        
        text_lower = text.lower().strip()
        
        # Too short or too long
        if len(text_lower) < 3 or len(text_lower) > 60:
            return False
        
        # Just a number
        if text_lower.replace('.', '').replace(',', '').isdigit():
            return False
        
        # Starts with number (likely "35 likes" or "50 beds")
        if text_lower.split()[0].replace('.', '').isdigit():
            return False
        
        # Location indicators
        location_patterns = [
            'located', 'location', 'address', 'road', 'street', 'avenue', 'lane',
            ' in accra', ' in ghana', ' at ', 'near ', 'opposite', 'behind',
            'estate', 'compound', 'region', 'district', 'area', 'zone',
            'gps:', 'coordinates:', 'latitude', 'longitude'
        ]
        if any(pattern in text_lower for pattern in location_patterns):
            return False
        
        # Management/ownership
        management_patterns = [
            'managed by', 'operated by', 'owned by', 'run by',
            'director:', 'manager:', 'contact:', 'phone:', 'email:'
        ]
        if any(pattern in text_lower for pattern in management_patterns):
            return False
        
        # Social media / likes / followers
        social_patterns = ['likes', 'followers', 'views', 'subscribers', 'facebook', 'twitter', 'instagram']
        if any(pattern in text_lower for pattern in social_patterns):
            return False
        
        # Must contain service-related keywords for validation
        service_keywords = [
            'service', 'care', 'emergency', 'outpatient', 'inpatient',
            'consultation', 'treatment', 'diagnostic', 'therapy',
            '24/7', '24-hour', 'ambulance', 'laboratory', 'lab',
            'pharmacy', 'ward', 'unit', 'department', 'clinic',
            'screening', 'testing', 'examination', 'monitoring'
        ]
        
        # If it has service keywords, it's valid
        if any(keyword in text_lower for keyword in service_keywords):
            return True
        
        # Otherwise reject (too risky to include)
        return False
    
    def _process_chunk(self, df_chunk: pd.DataFrame, use_llm: bool) -> Tuple[Dict, List]:
        """Process a chunk of rows. Returns (entities_dict, relationships_list)."""
        entities = {"facilities": []}
        relationships = []

        for idx, row in df_chunk.iterrows():
            # STAGE 1: Parse structured CSV data
            facility_data = self._parse_facility(row)
            csv_entities = self._extract_csv_entities(row, idx)
            
            # STAGE 2: LLM extraction from description (if enabled)
            llm_entities = {}
            if use_llm and self.llm_extractor and self.llm_extractor.enabled:
                desc = str(row.get('description', '')) if pd.notna(row.get('description')) else ''
                if len(desc) > 30:  # Only extract if description has content
                    llm_entities = self.llm_extractor.extract_entities(
                        facility_name=row['name'],
                        description=desc,
                        csv_data=csv_entities
                    )
                    
                    # STAGE 3: Validate and merge
                    merged_entities = self.validator.validate_and_merge(
                        csv_entities=csv_entities,
                        llm_entities=llm_entities,
                        facility_name=row['name']
                    )
                    
                    # Update facility with validated metadata
                    facility_data.update(merged_entities["metadata"])
                    facility_data["data_quality"] = {
                        "corrupted_fields": merged_entities["validation_report"]["corrupted_fields"],
                        "llm_enhanced": True
                    }
                else:
                    # No LLM extraction, use CSV only
                    merged_entities = self._csv_entities_to_merged_format(csv_entities)
                    facility_data["data_quality"] = {"llm_enhanced": False}
            else:
                # LLM disabled, use CSV only
                merged_entities = self._csv_entities_to_merged_format(csv_entities)
                facility_data["data_quality"] = {"llm_enhanced": False}
            
            # Add facility
            entities["facilities"].append(facility_data)
            
            # Parse location
            if pd.notna(row.get('address_city')) or pd.notna(row.get('address_stateOrRegion')):
                location = self._parse_location(row)
                
                # Auto-create collection if needed
                if "locations" not in entities:
                    entities["locations"] = []
                entities["locations"].append(location)
                
                # Create LOCATED_IN relationship
                relationships.append({
                    "source": row['name'],
                    "target": location['name'],
                    "type": "LOCATED_IN",
                    "confidence": 1.0,
                    "source_document": f"row_{idx}",
                    "evidence": f"Located in {location['name']}"
                })
            
            # Parse specialties from CSV (structured array)
            if pd.notna(row.get('specialties')):
                specialty_list = self._safe_parse_array(row['specialties'])
                for specialty_name in specialty_list:
                    specialty = {
                        "name": specialty_name,
                        "type": specialty_name,
                        "source_document": f"row_{idx}"
                    }
                    
                    # Auto-create collection if needed
                    if "specialties" not in entities:
                        entities["specialties"] = []
                    entities["specialties"].append(specialty)
                    
                    # Relationship
                    relationships.append({
                        "source": row['name'],
                        "target": specialty_name,
                        "type": "PROVIDES_SPECIALTY",
                        "confidence": 1.0,
                        "source_document": f"row_{idx}",
                        "evidence": f"Specializes in {specialty_name}"
                    })
            
            # Parse procedures from CSV (structured array)
            if pd.notna(row.get('procedure')):
                procedure_list = self._safe_parse_array(row['procedure'])
                for proc_str in procedure_list:
                    procedure = {
                        "name": proc_str,
                        "category": "general",
                        "source_document": f"row_{idx}"
                    }
                    
                    # Auto-create collection if needed
                    if "procedures" not in entities:
                        entities["procedures"] = []
                    entities["procedures"].append(procedure)
                    
                    relationships.append({
                        "source": row['name'],
                        "target": proc_str,
                        "type": "OFFERS_PROCEDURE",
                        "confidence": 1.0,
                        "source_document": f"row_{idx}",
                        "evidence": proc_str
                    })
            
            # Parse equipment from CSV (structured array)
            if pd.notna(row.get('equipment')):
                equipment_list = self._safe_parse_array(row['equipment'])
                for equip_str in equipment_list:
                    equipment, rel_type = self._parse_equipment(equip_str, idx)
                    
                    # Auto-create collection if needed
                    if "equipment" not in entities:
                        entities["equipment"] = []
                    entities["equipment"].append(equipment)
                    
                    relationships.append({
                        "source": row['name'],
                        "target": equipment['name'],
                        "type": rel_type,
                        "confidence": 0.9,
                        "source_document": f"row_{idx}",
                        "evidence": equip_str
                    })
            
            # Parse capabilities from CSV with intelligent classification
            if pd.notna(row.get('capability')):
                capability_list = self._safe_parse_array(row['capability'])
                for cap_str in capability_list:
                    # Use intelligent classifier to determine entity type and relationship
                    classification = self.classifier.classify_and_extract(row['name'], cap_str)
                    
                    if classification.get("skip", False):
                        logger.debug("Skipping '%s' (classified as irrelevant)", cap_str)
                        continue
                    
                    entity_type = classification["entity_type"]
                    entity_name = classification["entity_name"]
                    rel_type = classification["relationship_type"]
                    confidence = classification["confidence"]
                    
                    # Handle Metadata: attach to facility instead of creating entity
                    if entity_type == "Metadata":
                        # Add metadata to facility_data properties
                        if "metadata" not in facility_data:
                            facility_data["metadata"] = []
                        facility_data["metadata"].append(cap_str)
                        logger.debug("Metadata '%s' stored as facility property", cap_str)
                        continue
                    
                    # Map entity type to collection (dynamic with normalization)
                    entity_collection = self._normalize_entity_collection(entity_type)
                    
                    # Create entity with appropriate type
                    entity = {
                        "name": entity_name,
                        "type": entity_type.lower(),
                        "source_document": f"row_{idx}",
                        "data_source": "csv_classified"
                    }
                    
                    # Add to appropriate collection (create if doesn't exist)
                    if entity_collection not in entities:
                        entities[entity_collection] = []
                    entities[entity_collection].append(entity)
                    
                    # Create relationship with correct type
                    relationships.append({
                        "source": row['name'],
                        "target": entity_name,
                        "type": rel_type,
                        "confidence": confidence,
                        "source_document": f"row_{idx}",
                        "evidence": cap_str,
                        "data_source": "csv_classified"
                    })
                    
                    logger.debug("Classified '%s' -> %s (%s)", cap_str, entity_type, rel_type)
            
            # LLM ENHANCEMENT: Extract additional entities from description (if enabled and has description)
            if self.enable_llm_extraction and self.llm_extractor and self.llm_extractor.enabled:
                desc = str(row.get('description', '')) if pd.notna(row.get('description')) else ''
                if len(desc) > 50 and not desc.startswith('http'):
                    # Extract LLM entities
                    llm_entities = self.llm_extractor.extract_entities(
                        facility_name=row['name'],
                        description=desc,
                        csv_data=csv_entities
                    )
                    
                    # Add LLM-extracted entities (avoid duplicates with CSV)
                    csv_equipment_names = {item for item in csv_entities.get('equipment', [])}
                    csv_procedure_names = {item for item in csv_entities.get('procedures', [])}
                    csv_specialty_names = {item for item in csv_entities.get('specialties', [])}
                    csv_capability_names = {item for item in csv_entities.get('capabilities', [])}
                    
                    # Add LLM equipment not in CSV
                    for llm_equip in llm_entities.get("equipment", []):
                        equip_name = llm_equip["name"]
                        if equip_name.lower() not in {n.lower() for n in csv_equipment_names}:
                            if "equipment" not in entities:
                                entities["equipment"] = []
                            entities["equipment"].append({
                                "name": equip_name,
                                "equipment_type": "medical_device",
                                "status": "available",
                                "data_source": "llm",
                                "confidence": llm_equip["confidence"],
                                "source_document": f"row_{idx}_llm"
                            })
                            relationships.append({
                                "source": row['name'],
                                "target": equip_name,
                                "type": "HAS_EQUIPMENT",
                                "confidence": llm_equip["confidence"],
                                "data_source": "llm",
                                "source_document": f"row_{idx}_llm",
                                "evidence": f"Extracted from description"
                            })
                    
                    # Add LLM procedures not in CSV
                    for llm_proc in llm_entities.get("procedures", []):
                        proc_name = llm_proc["name"]
                        if proc_name.lower() not in {n.lower() for n in csv_procedure_names}:
                            if "procedures" not in entities:
                                entities["procedures"] = []
                            entities["procedures"].append({
                                "name": proc_name,
                                "category": "general",
                                "data_source": "llm",
                                "confidence": llm_proc["confidence"],
                                "source_document": f"row_{idx}_llm"
                            })
                            relationships.append({
                                "source": row['name'],
                                "target": proc_name,
                                "type": "OFFERS_PROCEDURE",
                                "confidence": llm_proc["confidence"],
                                "data_source": "llm",
                                "source_document": f"row_{idx}_llm",
                                "evidence": f"Extracted from description"
                            })
                    
                    # Add LLM specialties not in CSV
                    for llm_spec in llm_entities.get("specialties", []):
                        spec_name = llm_spec["name"]
                        if spec_name.lower() not in {n.lower() for n in csv_specialty_names}:
                            if "specialties" not in entities:
                                entities["specialties"] = []
                            entities["specialties"].append({
                                "name": spec_name,
                                "type": spec_name,
                                "data_source": "llm",
                                "confidence": llm_spec["confidence"],
                                "source_document": f"row_{idx}_llm"
                            })
                            relationships.append({
                                "source": row['name'],
                                "target": spec_name,
                                "type": "PROVIDES_SPECIALTY",
                                "confidence": llm_spec["confidence"],
                                "data_source": "llm",
                                "source_document": f"row_{idx}_llm",
                                "evidence": f"Extracted from description"
                            })
                    
                    # Add LLM capabilities not in CSV (with validation)
                    for llm_cap in llm_entities.get("capabilities", []):
                        cap_name = llm_cap["name"]
                        
                        # Skip if already in CSV
                        if cap_name.lower() in {n.lower() for n in csv_capability_names}:
                            continue
                        
                        # Validate it's actually a service capability
                        if not self._is_valid_capability(cap_name):
                            logger.debug("Skipping LLM capability '%s' (invalid)", cap_name)
                            continue
                        
                        if "capabilities" not in entities:
                            entities["capabilities"] = []
                        entities["capabilities"].append({
                            "name": cap_name,
                            "type": "general",
                            "data_source": "llm",
                            "confidence": llm_cap["confidence"],
                            "source_document": f"row_{idx}_llm"
                        })
                        relationships.append({
                            "source": row['name'],
                            "target": cap_name,
                            "type": "HAS_CAPABILITY",
                            "confidence": llm_cap["confidence"],
                            "data_source": "llm",
                            "source_document": f"row_{idx}_llm",
                            "evidence": f"Extracted from description"
                        })
        return entities, relationships

    def parse_csv(self, csv_path: str, enable_llm: bool = None) -> Tuple[Dict, List]:
        """
        Parse VF CSV into KG entities and relationships.
        Uses chunked parallel processing for large files.
        """
        use_llm = enable_llm if enable_llm is not None else self.enable_llm_extraction
        df = pd.read_csv(csv_path)
        total_rows = len(df)
        logger.info("Loaded %d facilities from CSV", total_rows)

        num_workers = int(os.environ.get("CSV_CHUNK_WORKERS", "4"))
        num_workers = min(max(1, num_workers), 16)
        chunk_size = max(1, (total_rows + num_workers - 1) // num_workers)
        chunks = [df.iloc[i:i + chunk_size] for i in range(0, total_rows, chunk_size)]

        entities = {"facilities": []}
        relationships = []

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {executor.submit(self._process_chunk, chunk, use_llm): chunk for chunk in chunks}
            for future in as_completed(futures):
                chunk_entities, chunk_rels = future.result()
                for k, v in chunk_entities.items():
                    entities.setdefault(k, []).extend(v)
                relationships.extend(chunk_rels)

        # Deduplicate entities
        for entity_type in entities:
            entities[entity_type] = self._deduplicate(entities[entity_type])

        # Build entity name lookup (case-insensitive and stripped)
        entity_name_map = {}  # normalized_name -> actual_name
        for f in entities.get('facilities', []):
            normalized = f['name'].strip().lower()
            entity_name_map[normalized] = f['name']
        for e in entities.get('equipment', []):
            normalized = e['name'].strip().lower()
            entity_name_map[normalized] = e['name']
        for p in entities.get('procedures', []):
            normalized = p['name'].strip().lower()
            entity_name_map[normalized] = p['name']
        for s in entities.get('specialties', []):
            normalized = s['name'].strip().lower()
            entity_name_map[normalized] = s['name']
        for c in entities.get('capabilities', []):
            normalized = c['name'].strip().lower()
            entity_name_map[normalized] = c['name']
        for l in entities.get('locations', []):
            normalized = l['name'].strip().lower()
            entity_name_map[normalized] = l['name']
        
        # Add all other dynamic entity types to the lookup
        for entity_type, entity_list in entities.items():
            if entity_type not in ['facilities', 'equipment', 'procedures', 'specialties', 'capabilities', 'locations']:
                for entity in entity_list:
                    if 'name' in entity:
                        normalized = entity['name'].strip().lower()
                        entity_name_map[normalized] = entity['name']
        
        # Normalize relationship references
        normalized_relationships = []
        orphaned_count = 0
        
        for rel in relationships:
            source_norm = rel['source'].strip().lower()
            target_norm = rel['target'].strip().lower()
            
            # Check if both source and target exist (case-insensitive)
            if source_norm in entity_name_map and target_norm in entity_name_map:
                # Update relationship to use canonical entity names
                rel['source'] = entity_name_map[source_norm]
                rel['target'] = entity_name_map[target_norm]
                normalized_relationships.append(rel)
            else:
                orphaned_count += 1
                if orphaned_count <= 5:  # Show first few for debugging
                    missing = []
                    if source_norm not in entity_name_map:
                        missing.append(f"source: {rel['source']}")
                    if target_norm not in entity_name_map:
                        missing.append(f"target: {rel['target']}")
                    logger.debug("Orphaned relationship: %s", ' + '.join(missing))
        
        relationships = normalized_relationships
        
        if orphaned_count > 0:
            logger.info("Removed %d orphaned relationships", orphaned_count)
        
        logger.info("Extracted: %s entity types, %d relationships", len(entities), len(relationships))
        
        return entities, relationships
    
    def _parse_facility(self, row: pd.Series) -> Dict:
        """Parse facility from row"""
        # Helper to safely get values, converting NaN to None
        def safe_get(key, default=None):
            val = row.get(key, default)
            if pd.isna(val):
                return None
            return val
        
        def safe_int(key):
            val = row.get(key)
            if pd.notna(val):
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return None
            return None
        
        return {
            "name": str(row['name']) if pd.notna(row.get('name')) else '',
            "facility_type": safe_get('facilityTypeId'),
            "operator_type": safe_get('operatorTypeId'),
            "capacity": safe_int('capacity'),
            "number_doctors": safe_int('numberDoctors'),
            "description": safe_get('description'),
            "official_phone": safe_get('phone_numbers'),
            "email": safe_get('email'),
            "official_website": safe_get('officialWebsite'),
            "year_established": safe_int('yearEstablished'),
            "source_document": safe_get('source_url', 'csv')
        }
    
    def _parse_location(self, row: pd.Series) -> Dict:
        """Parse location from row"""
        # Build location name
        parts = []
        city = None
        state = None
        
        if pd.notna(row.get('address_city')):
            city = str(row['address_city']).strip()
            parts.append(city)
        
        if pd.notna(row.get('address_stateOrRegion')):
            state = str(row['address_stateOrRegion']).strip()
            parts.append(state)
        
        location_name = ", ".join(parts) if parts else row.get('address_country', 'Unknown')
        
        return {
            "name": location_name,
            "city": city if city else "Unknown",
            "state_or_region": state if state else "Unknown",
            "country": row.get('address_country', 'Ghana'),
            "country_code": row.get('address_countryCode', 'GH'),
            "source_document": row.get('source_url', 'csv')
        }
    
    def _safe_parse_array(self, value: str) -> List:
        """Safely parse string representation of array"""
        if pd.isna(value) or value == '' or value == '[]':
            return []
        
        try:
            # Try to parse as JSON array
            if isinstance(value, str):
                parsed = json.loads(value.replace("'", '"'))
                return parsed if isinstance(parsed, list) else []
            elif isinstance(value, list):
                return value
        except:
            try:
                # Try ast.literal_eval
                return ast.literal_eval(value)
            except:
                # Last resort: split by comma
                return [v.strip() for v in str(value).split(',')]
        
        return []
    
    def _parse_equipment(self, equip_str: str, row_idx: int) -> Tuple[Dict, str]:
        """
        Parse equipment string and determine if HAS or LACKS
        
        Returns:
            (equipment_dict, relationship_type)
        """
        equip_str_lower = equip_str.lower()
        
        # Determine if HAS or LACKS
        lacks_indicators = ['lack', 'no ', 'without', 'missing', 'absent', 'unavailable', 'broken']
        rel_type = "HAS_EQUIPMENT"
        
        for indicator in lacks_indicators:
            if indicator in equip_str_lower:
                rel_type = "LACKS_EQUIPMENT"
                break
        
        # Clean equipment name
        equipment_name = equip_str
        for indicator in lacks_indicators:
            equipment_name = equipment_name.replace(indicator, '').strip()
        
        # Determine type
        equip_type = "medical_device"
        if any(x in equip_str_lower for x in ['ct', 'mri', 'x-ray', 'ultrasound', 'scanner']):
            equip_type = "diagnostic_imaging"
        elif any(x in equip_str_lower for x in ['ventilator', 'oxygen', 'icu']):
            equip_type = "life_support"
        
        equipment = {
            "name": equipment_name,
            "equipment_type": equip_type,
            "status": "lacking" if rel_type == "LACKS_EQUIPMENT" else "available",
            "source_document": f"row_{row_idx}",
            "original_text": equip_str
        }
        
        return equipment, rel_type
    
    def _extract_from_description(self, facility_name: str, description: str, row_idx: int) -> Tuple[Dict, List]:
        """Extract additional entities from free-text description using LLM"""
        
        if not self.llm:
            return {"equipment": [], "capabilities": []}, []
        
        prompt = f"""Extract medical information from this facility description.

FACILITY: {facility_name}
DESCRIPTION: {description}

Extract:
1. EQUIPMENT mentioned (devices, machines, infrastructure)
2. GAPS or LACKS (missing equipment, unavailable services)
3. CAPABILITIES (services, care levels, accreditations)

Return ONLY valid JSON:
{{
    "equipment": [
        {{"name": "...", "status": "has|lacks"}}
    ],
    "capabilities": [
        {{"name": "..."}}
    ]
}}

Focus on explicit mentions. If nothing found, return empty arrays."""

        messages = [
            SystemMessage(content="You are a medical data extractor. Return only valid JSON."),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            content = response.content
            
            # Handle empty or whitespace-only responses
            if not content or not content.strip():
                logger.debug("LLM returned empty response for %s", facility_name)
                return {"equipment": [], "capabilities": []}, []
            
            # Extract JSON from markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            content = content.strip()
            if not content:
                return {"equipment": [], "capabilities": []}, []
            
            result = json.loads(content)
            
            entities = {
                "equipment": [],
                "capabilities": []
            }
            relationships = []
            
            # Process extracted equipment
            for equip in result.get('equipment', []):
                equip_dict = {
                    "name": equip['name'],
                    "equipment_type": "medical_device",
                    "status": equip.get('status', 'unknown'),
                    "source_document": f"row_{row_idx}_description"
                }
                entities["equipment"].append(equip_dict)
                
                rel_type = "LACKS_EQUIPMENT" if equip.get('status') == 'lacks' else "HAS_EQUIPMENT"
                relationships.append({
                    "source": facility_name,
                    "target": equip['name'],
                    "type": rel_type,
                    "confidence": 0.8,
                    "source_document": f"row_{row_idx}_description",
                    "evidence": description[:200]
                })
            
            # Process capabilities
            for cap in result.get('capabilities', []):
                cap_dict = {
                    "name": cap['name'],
                    "type": "general",
                    "source_document": f"row_{row_idx}_description"
                }
                entities["capabilities"].append(cap_dict)
                
                relationships.append({
                    "source": facility_name,
                    "target": cap['name'],
                    "type": "HAS_CAPABILITY",
                    "confidence": 0.8,
                    "source_document": f"row_{row_idx}_description",
                    "evidence": description[:200]
                })
            
            return entities, relationships
        
        except Exception as e:
            logger.warning("LLM extraction failed for %s: %s", facility_name, e)
            return {"equipment": [], "capabilities": []}, []
    
    def _deduplicate(self, entity_list: List[Dict]) -> List[Dict]:
        """Deduplicate entities by name"""
        seen = set()
        unique = []
        for entity in entity_list:
            name = entity.get('name', '')
            if name and name not in seen:
                seen.add(name)
                unique.append(entity)
        return unique
    def _extract_csv_entities(self, row: pd.Series, idx: int) -> Dict:
        """Extract entities from CSV structured fields"""
        entities = {
            "equipment": [],
            "procedures": [],
            "specialties": [],
            "capabilities": [],
            "capacity": self._safe_int(row.get('capacity')),
            "facility_type": self._safe_get(row, 'facilityTypeId'),
            "operator_type": self._safe_get(row, 'operatorTypeId'),
            "number_doctors": self._safe_int(row.get('numberDoctors'))
        }
        
        # Parse equipment
        if pd.notna(row.get('equipment')):
            equipment_list = self._safe_parse_array(row['equipment'])
            entities["equipment"] = [item for item in equipment_list if item]
        
        # Parse procedures
        if pd.notna(row.get('procedure')):
            procedure_list = self._safe_parse_array(row['procedure'])
            entities["procedures"] = [item for item in procedure_list if item]
        
        # Parse specialties
        if pd.notna(row.get('specialties')):
            specialty_list = self._safe_parse_array(row['specialties'])
            entities["specialties"] = [item for item in specialty_list if item]
        
        # Parse capabilities
        if pd.notna(row.get('capability')):
            capability_list = self._safe_parse_array(row['capability'])
            entities["capabilities"] = [item for item in capability_list if item]
        
        return entities
    
    def _csv_entities_to_merged_format(self, csv_entities: Dict) -> Dict:
        """Convert CSV entities to merged format when LLM is disabled"""
        merged = {
            "equipment": [],
            "procedures": [],
            "specialties": [],
            "capabilities": [],
            "metadata": {}
        }
        
        for entity_type in ["equipment", "procedures", "specialties", "capabilities"]:
            for item in csv_entities.get(entity_type, []):
                merged[entity_type].append({
                    "name": item,
                    "source": "csv",
                    "confidence": 1.0
                })
        
        # Copy metadata
        merged["metadata"] = {
            "capacity": csv_entities.get("capacity"),
            "facility_type": csv_entities.get("facility_type"),
            "operator_type": csv_entities.get("operator_type"),
            "number_doctors": csv_entities.get("number_doctors")
        }
        
        return merged
    
    def _safe_get(self, row: pd.Series, key: str, default=None):
        """Safely get value from row"""
        val = row.get(key, default)
        if pd.isna(val):
            return None
        return val
    
    def _normalize_entity_collection(self, entity_type: str) -> str:
        """Convert entity type to normalized collection name (snake_case plural)"""
        # Common mappings
        standard_mappings = {
            "Location": "locations",
            "Contact": "contacts",
            "Operator": "operators",
            "TemporalInfo": "temporal_info",
            "StaffingInfo": "staffing_info",
            "Capability": "capabilities",
            "Equipment": "equipment",
            "Specialty": "specialties",
            "Procedure": "procedures",
            "Facility": "facilities",
        }
        
        if entity_type in standard_mappings:
            return standard_mappings[entity_type]
        
        # For new types: convert to snake_case and pluralize
        # CamelCase -> snake_case
        import re
        snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', entity_type).lower()
        
        # Simple pluralization (add 's' if not already plural)
        if not snake_case.endswith('s') and not snake_case.endswith('_info'):
            snake_case += 's'
        
        return snake_case
    
    def _safe_int(self, value) -> int:
        """Safely convert to int"""
        if pd.notna(value):
            try:
                # Convert to string and check if numeric
                str_val = str(value).strip()
                if str_val.replace('-', '').replace('+', '').replace('.', '').isdigit():
                    return int(float(str_val))
                return None
            except (ValueError, TypeError):
                return None
        return None
