"""
Intelligent Relationship Classification Service
Uses LLM to classify text and infer appropriate entity types and relationships.
Supports Gemini (free tier), OpenAI, Anthropic, and Ollama via llm_factory.
"""

import re
from typing import Dict, Tuple, Optional
from langchain_core.messages import HumanMessage, SystemMessage
import json
import os

from .llm_factory import get_llm


class RelationshipClassifier:
    """Classify text fragments and infer appropriate relationships"""
    
    def __init__(self, provider=None, model=None):
        """
        Initialize with LLM provider (from env LLM_PROVIDER if not set).

        Args:
            provider: "gemini" (free), "openai", "anthropic", or "ollama"
            model: Model name (optional, uses env defaults)
        """
        try:
            self.llm = get_llm(provider=provider or os.getenv("LLM_PROVIDER", "ollama"), model=model, temperature=0.0)
            if self.llm:
                self.enabled = True
                prov = (provider or os.getenv("LLM_PROVIDER", "ollama")).lower()
                print(f"✓ Relationship classifier using {prov}")
            else:
                self.llm = None
                self.enabled = False
                print("⚠️  No LLM available. Run Ollama (ollama serve) and set OLLAMA_MODEL in .env")
        except Exception as e:
            print(f"⚠️  Could not initialize LLM classifier: {e}")
            self.llm = None
            self.enabled = False
    
    def classify_and_extract(self, facility_name: str, text: str) -> Dict:
        """
        Classify text and determine entity type and relationship
        
        Args:
            facility_name: The facility this text relates to
            text: The text to classify (e.g., "Located in Accra", "35 likes", "Contact: 0201234567")
        
        Returns:
            {
                "entity_type": str,  # "Location", "Contact", "SocialMetric", "Capability", etc.
                "entity_name": str,  # Cleaned entity name
                "relationship_type": str,  # "LOCATED_IN", "HAS_CONTACT", "HAS_SOCIAL_METRIC", etc.
                "confidence": float,
                "skip": bool  # True if should be skipped entirely
            }
        """
        if not self.enabled:
            return self._fallback_classify(text)
        
        try:
            # Quick pattern-based classification for common cases (faster)
            quick_result = self._quick_classify(text)
            if quick_result:
                return quick_result
            
            # Use LLM for ambiguous cases
            return self._llm_classify(facility_name, text)
            
        except Exception as e:
            print(f"Error classifying '{text}': {e}")
            return self._fallback_classify(text)
    
    def _quick_classify(self, text: str) -> Optional[Dict]:
        """Fast pattern-based classification for obvious cases"""
        text_lower = text.lower().strip()
        
        # Skip completely useless data
        if len(text_lower) < 3 or text_lower.replace('.', '').replace(',', '').isdigit():
            return {"skip": True}
        
        # Location patterns
        location_patterns = [
            r'located\s+(in|at|near)',
            r'address:?\s*',
            r'\d+\s+\w+\s+(road|street|avenue|lane)',
            r'(accra|kumasi|tamale|cape coast|tema)',  # Ghana cities
            r'(estate|compound|area|region|district)',
            r'gps\s*:',
            r'coordinates'
        ]
        for pattern in location_patterns:
            if re.search(pattern, text_lower):
                # Extract location name
                location = re.sub(r'^(located\s+(in|at|near)|address:?\s*)', '', text_lower).strip()
                return {
                    "entity_type": "Location",
                    "entity_name": location.title(),
                    "relationship_type": "LOCATED_IN",
                    "confidence": 0.95,
                    "skip": False
                }
        
        # Contact patterns
        contact_patterns = [
            r'(phone|tel|mobile|contact):?\s*[\d\s\-+()]+',
            r'\+?\d{3}[\s\-]?\d{3}[\s\-]?\d{4}',  # Phone format
            r'email:?\s*\S+@\S+',
            r'contact:?\s*',
        ]
        for pattern in contact_patterns:
            if re.search(pattern, text_lower):
                # Extract contact info
                contact = re.sub(r'^(phone|tel|mobile|contact|email):?\s*', '', text).strip()
                return {
                    "entity_type": "Contact",
                    "entity_name": contact,
                    "relationship_type": "HAS_CONTACT",
                    "confidence": 0.95,
                    "skip": False
                }
        
        # Operational hours / Always open
        if re.search(r'(always|24/7|24-hour)\s*(open|available)', text_lower):
            return {
                "entity_type": "Capability",
                "entity_name": "24/7 Service",
                "relationship_type": "HAS_CAPABILITY",
                "confidence": 0.95,
                "skip": False
            }
        
        # Temporal data (founding, establishment dates)
        temporal_patterns = [
            r'(established|founded|opened|started|began)\s+(in|on|at)?\s*',
            r'(since|from)\s+\d{4}',
            r'\d{4}\s*-\s*(present|now)',
            r'(created|registered)\s+(in|on)\s+\w+\s+\d+,?\s+\d{4}',
        ]
        for pattern in temporal_patterns:
            if re.search(pattern, text_lower):
                # Extract date/year
                temporal_info = re.sub(r'^(established|founded|opened|started|began|since|from|page\s+created|registered)\s+(in|on|at)?\s*', '', text).strip()
                return {
                    "entity_type": "TemporalInfo",
                    "entity_name": temporal_info.title(),
                    "relationship_type": "ESTABLISHED_ON",
                    "confidence": 0.9,
                    "skip": False
                }
        
        # Staffing/size information
        staffing_patterns = [
            r'has\s+\d+[\s\-]*\d*\s+(employees|staff|workers|doctors|nurses)',
            r'\d+[\s\-]*\d*\s+(employees|staff|workers|doctors|nurses)',
            r'(team|staff)\s+(of|size)',
        ]
        for pattern in staffing_patterns:
            if re.search(pattern, text_lower):
                # Extract staffing info
                staffing = re.sub(r'^has\s+', '', text).strip()
                return {
                    "entity_type": "StaffingInfo",
                    "entity_name": staffing.title(),
                    "relationship_type": "HAS_STAFFING",
                    "confidence": 0.9,
                    "skip": False
                }
        
        # Metadata patterns (social metrics, data sources, page status)
        metadata_patterns = [
            r'\d+\s*(likes|followers|views|subscribers|check-ins)',
            r'(listed|categorized|mentioned)\s+(as|on|in)',
            r'(facebook|twitter|instagram|web)\s*(page|profile)',
            r'is\s+(an?\s+)?(official|unofficial)\s+page',
            r'page\s+(created|status|shows)',
            r'data\s+source:?',
        ]
        for pattern in metadata_patterns:
            if re.search(pattern, text_lower):
                return {
                    "entity_type": "Metadata",
                    "entity_name": text.strip(),
                    "relationship_type": None,  # Will be stored as facility property
                    "confidence": 0.8,
                    "skip": False
                }
        
        # Management/ownership
        if re.search(r'(managed|operated|owned|run)\s+by', text_lower):
            operator = re.sub(r'^.*(managed|operated|owned|run)\s+by\s*', '', text).strip()
            return {
                "entity_type": "Operator",
                "entity_name": operator.title(),
                "relationship_type": "MANAGED_BY",
                "confidence": 0.9,
                "skip": False
            }
        
        # Insurance partnerships
        if re.search(r'insurance\s+(partnership|provider|accept|cover)', text_lower):
            return {
                "entity_type": "Capability",
                "entity_name": text.strip(),
                "relationship_type": "HAS_CAPABILITY",
                "confidence": 0.85,
                "skip": False
            }
        
        # Service capabilities
        service_keywords = [
            'emergency', 'outpatient', 'inpatient', 'consultation',
            'treatment', '24/7', '24-hour', 'ambulance', 'laboratory',
            'pharmacy', 'diagnostic', 'screening', 'testing'
        ]
        if any(kw in text_lower for kw in service_keywords):
            return {
                "entity_type": "Capability",
                "entity_name": text.strip(),
                "relationship_type": "HAS_CAPABILITY",
                "confidence": 0.9,
                "skip": False
            }
        
        # Unclear - use LLM
        return None
    
    def _llm_classify(self, facility_name: str, text: str) -> Dict:
        """Use LLM to classify ambiguous text"""
        
        prompt = f"""Classify this text fragment from a healthcare facility description.

Facility: {facility_name}
Text: "{text}"

Determine:
1. What type of information is this?
2. What entity should be created?
3. What relationship type should connect the facility to this entity?

Entity Types:
- Location: Address, city, region, area
- Contact: Phone, email, contact person, website
- Operator: Who manages/operates the facility
- TemporalInfo: Founding date, establishment year, opening date
- StaffingInfo: Number of employees, staff size, team size
- Capability: Service capability (actual medical services, hours of operation)
- Equipment: Medical equipment
- Specialty: Medical specialty
- Metadata: Social media metrics, data source references, page status, unofficial/official tags (will be stored as facility properties, not separate entities)

Relationship Types:
- LOCATED_IN: For locations
- HAS_CONTACT: For contact information
- MANAGED_BY: For operators/management
- ESTABLISHED_ON: For founding/establishment dates
- HAS_STAFFING: For employee count and staffing information
- HAS_CAPABILITY: For service capabilities
- HAS_EQUIPMENT: For equipment
- PROVIDES_SPECIALTY: For specialties

Return JSON:
{{
  "entity_type": "...",
  "entity_name": "cleaned entity name",
  "relationship_type": "...",
  "confidence": 0.0-1.0,
  "skip": false,
  "reasoning": "brief explanation"
}}

If this should be skipped (social metrics, junk), return:
{{"skip": true, "reasoning": "why"}}
"""

        try:
            messages = [
                SystemMessage(content="You are a data classification expert for healthcare systems."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            result = self._parse_llm_response(response.content)
            return result
            
        except Exception as e:
            print(f"LLM classification error: {e}")
            return self._fallback_classify(text)
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM JSON response"""
        try:
            # Extract JSON from response
            response = response.strip()
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()
            
            data = json.loads(response)
            
            # Validate and set defaults
            if data.get("skip", False):
                return {"skip": True}
            
            return {
                "entity_type": data.get("entity_type", "Unknown"),
                "entity_name": data.get("entity_name", "").strip(),
                "relationship_type": data.get("relationship_type", "RELATED_TO"),
                "confidence": float(data.get("confidence", 0.7)),
                "skip": False
            }
            
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return self._fallback_classify("")
    
    def _fallback_classify(self, text: str) -> Dict:
        """Fallback classification when LLM unavailable"""
        # Very conservative - treat as capability if has service keywords, else skip
        service_keywords = ['service', 'care', 'emergency', 'patient', 'medical', 'health']
        
        if any(kw in text.lower() for kw in service_keywords):
            return {
                "entity_type": "Capability",
                "entity_name": text.strip(),
                "relationship_type": "HAS_CAPABILITY",
                "confidence": 0.6,
                "skip": False
            }
        else:
            return {"skip": True}
