"""
Entity Validation and Deduplication Service
Validates and normalizes extracted entities
"""

import re
from typing import Dict, List, Set
from difflib import SequenceMatcher


class EntityValidator:
    """Validate and deduplicate healthcare entities"""
    
    def __init__(self):
        # Common corrupted data patterns
        self.invalid_patterns = {
            'capacity': r'[a-zA-Z]+',  # Capacity should be numeric only
            'number_doctors': r'[a-zA-Z]+',
        }
        
        # Entity normalization rules
        self.normalization_rules = {
            'equipment': {
                'ultrasound machine': 'Ultrasound',
                'us equipment': 'Ultrasound',
                'general ultrasound': 'Ultrasound',
                'x-ray machine': 'X-ray',
                'xray': 'X-ray',
                'ct scan': 'CT Scanner',
                'mri machine': 'MRI',
            },
            'procedures': {
                'general surgery': 'Surgery',
                'surgical procedures': 'Surgery',
                'emergency services': 'Emergency Care',
                'er services': 'Emergency Care',
            },
            'specialties': {
                'general practice': 'General Medicine',
                'gp': 'General Medicine',
                'internal medicine': 'Internal Medicine',
            }
        }
    
    def validate_and_merge(
        self, 
        csv_entities: Dict, 
        llm_entities: Dict, 
        facility_name: str
    ) -> Dict:
        """
        Validate and merge CSV and LLM extracted entities
        
        Args:
            csv_entities: Entities from CSV parsing
            llm_entities: Entities from LLM extraction
            facility_name: Name of facility (for logging)
        
        Returns:
            Merged and validated entity dict with metadata
        """
        merged = {
            "equipment": [],
            "procedures": [],
            "specialties": [],
            "capabilities": [],
            "metadata": {},
            "validation_report": {
                "corrupted_fields": [],
                "duplicates_removed": 0,
                "llm_additions": 0,
                "csv_only": 0,
                "llm_only": 0,
                "both_sources": 0
            }
        }
        
        # Validate numeric fields
        corrupted = self._validate_numeric_fields(csv_entities)
        merged["validation_report"]["corrupted_fields"] = corrupted
        
        # Merge each entity type
        for entity_type in ["equipment", "procedures", "specialties", "capabilities"]:
            csv_items = csv_entities.get(entity_type, [])
            llm_items = [item["name"] for item in llm_entities.get(entity_type, [])]
            
            # Normalize and deduplicate
            merged_items, stats = self._merge_entity_list(
                csv_items, 
                llm_items, 
                entity_type
            )
            
            merged[entity_type] = merged_items
            merged["validation_report"]["duplicates_removed"] += stats["duplicates"]
            merged["validation_report"]["llm_additions"] += stats["llm_only"]
            merged["validation_report"]["csv_only"] += stats["csv_only"]
            merged["validation_report"]["both_sources"] += stats["both"]
        
        # Merge metadata
        merged["metadata"] = self._merge_metadata(
            csv_entities, 
            llm_entities.get("metadata", {})
        )
        
        return merged
    
    def _validate_numeric_fields(self, csv_entities: Dict) -> List[str]:
        """Detect corrupted numeric fields"""
        corrupted = []
        
        for field, pattern in self.invalid_patterns.items():
            value = csv_entities.get(field)
            if value and isinstance(value, str) and re.search(pattern, value):
                corrupted.append(f"{field}: '{value}' contains non-numeric data")
        
        return corrupted
    
    def _merge_entity_list(
        self, 
        csv_items: List[str], 
        llm_items: List[str], 
        entity_type: str
    ) -> tuple[List[Dict], Dict]:
        """
        Merge and deduplicate entity lists from CSV and LLM
        
        Returns:
            (merged_list, stats)
        """
        stats = {
            "duplicates": 0,
            "llm_only": 0,
            "csv_only": 0,
            "both": 0
        }
        
        # Normalize all items
        normalized_csv = {self._normalize_entity(item, entity_type): item 
                         for item in csv_items if item}
        normalized_llm = {self._normalize_entity(item, entity_type): item 
                         for item in llm_items if item}
        
        # Track sources
        result = []
        seen = set()
        
        # Process CSV items
        for norm_name, original_name in normalized_csv.items():
            if norm_name not in seen:
                seen.add(norm_name)
                source = "both" if norm_name in normalized_llm else "csv"
                if source == "both":
                    stats["both"] += 1
                else:
                    stats["csv_only"] += 1
                
                result.append({
                    "name": original_name,
                    "normalized": norm_name,
                    "source": source,
                    "confidence": 1.0 if source == "both" else 0.7
                })
        
        # Process LLM-only items
        for norm_name, original_name in normalized_llm.items():
            if norm_name not in seen:
                seen.add(norm_name)
                stats["llm_only"] += 1
                result.append({
                    "name": original_name,
                    "normalized": norm_name,
                    "source": "llm",
                    "confidence": 0.8
                })
        
        # Count duplicates
        stats["duplicates"] = (len(normalized_csv) + len(normalized_llm)) - len(seen)
        
        return result, stats
    
    def _normalize_entity(self, name: str, entity_type: str) -> str:
        """Normalize entity name"""
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower().strip()
        
        # Apply normalization rules
        rules = self.normalization_rules.get(entity_type, {})
        if normalized in rules:
            normalized = rules[normalized].lower()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _merge_metadata(self, csv_entities: Dict, llm_metadata: Dict) -> Dict:
        """Merge metadata from CSV and LLM"""
        merged = {}
        
        # Capacity: Trust LLM if CSV is corrupted, else trust CSV
        csv_capacity = csv_entities.get("capacity")
        llm_capacity = llm_metadata.get("capacity")
        
        if csv_capacity and isinstance(csv_capacity, int):
            merged["capacity"] = csv_capacity
            merged["capacity_source"] = "csv"
        elif llm_capacity and isinstance(llm_capacity, int):
            merged["capacity"] = llm_capacity
            merged["capacity_source"] = "llm"
        else:
            merged["capacity"] = None
            merged["capacity_source"] = "none"
        
        # Facility type
        merged["facility_type"] = csv_entities.get("facility_type") or llm_metadata.get("facility_type")
        merged["operator_type"] = csv_entities.get("operator_type")
        merged["number_doctors"] = csv_entities.get("number_doctors")
        
        # Additional LLM insights
        if "extracted_info" in llm_metadata:
            merged["llm_summary"] = llm_metadata["extracted_info"]
        
        return merged
    
    def fuzzy_match(self, str1: str, str2: str, threshold: float = 0.85) -> bool:
        """Check if two strings are similar enough to be duplicates"""
        ratio = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
        return ratio >= threshold
