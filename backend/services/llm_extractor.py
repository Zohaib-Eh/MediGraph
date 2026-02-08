"""
LLM-based Entity Extraction Service
Extracts entities from facility descriptions using LLM
"""

import json
from typing import Dict, List, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage


class LLMExtractor:
    """Extract healthcare entities from text using LLM"""
    
    def __init__(self, model="llama3.2"):
        try:
            self.llm = ChatOllama(
                model=model,
                temperature=0.0,
            )
            self.enabled = True
        except Exception as e:
            print(f"Warning: Could not initialize LLM for extraction: {e}")
            self.llm = None
            self.enabled = False
    
    def extract_entities(
        self, 
        facility_name: str, 
        description: str, 
        csv_data: Optional[Dict] = None
    ) -> Dict:
        """
        Extract entities from facility description
        
        Args:
            facility_name: Name of the facility
            description: Facility description text
            csv_data: Optional CSV-parsed data for context
        
        Returns:
            {
                "equipment": [{"name": str, "confidence": float}],
                "procedures": [{"name": str, "confidence": float}],
                "specialties": [{"name": str, "confidence": float}],
                "capabilities": [{"name": str, "confidence": float}],
                "metadata": {
                    "capacity": int | None,
                    "facility_type": str | None,
                    "extracted_info": str
                }
            }
        """
        if not self.enabled or not description or description.strip() == "":
            return self._empty_result()
        
        try:
            # Build extraction prompt
            prompt = self._build_extraction_prompt(facility_name, description, csv_data)
            
            # Call LLM
            messages = [
                SystemMessage(content="You are a medical data extraction expert. Extract structured information from healthcare facility descriptions."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Parse response
            extracted = self._parse_llm_response(response.content)
            
            return extracted
            
        except Exception as e:
            print(f"Error in LLM extraction for {facility_name}: {e}")
            return self._empty_result()
    
    def _build_extraction_prompt(
        self, 
        facility_name: str, 
        description: str, 
        csv_data: Optional[Dict]
    ) -> str:
        """Build extraction prompt"""
        
        csv_context = ""
        if csv_data:
            csv_context = f"""
CSV Data Available:
- Equipment: {json.dumps(csv_data.get('equipment', []))}
- Procedures: {json.dumps(csv_data.get('procedures', []))}
- Specialties: {json.dumps(csv_data.get('specialties', []))}
- Capacity: {csv_data.get('capacity', 'Unknown')}
"""
        
        prompt = f"""Extract healthcare entities from this facility description.

Facility Name: {facility_name}
Description: {description}

{csv_context}

Extract the following and return as JSON:
1. **equipment**: Medical equipment/devices (e.g., "Ultrasound", "X-ray machine", "MRI", "ECG")
2. **procedures**: Medical procedures/services (e.g., "Surgery", "Consultation", "Emergency care", "Lab tests")
3. **specialties**: Medical specialties (e.g., "Cardiology", "Pediatrics", "General Practice", "Obstetrics")
4. **capabilities**: Service capabilities ONLY - NOT locations (e.g., "24/7 Emergency", "Outpatient services", "Inpatient care", "Ambulance service")
5. **metadata**: Extract capacity (number of beds), facility type, and any other relevant info

CRITICAL RULES:
- DO NOT extract address/location information as capabilities
- Capabilities are SERVICES, not places or descriptions
- Location descriptions (streets, areas, cities) should be IGNORED
- Only extract entities explicitly mentioned in the description
- Use standardized medical terminology
- Return empty lists if nothing is mentioned
- Be conservative - don't hallucinate entities
- Validate capacity is a number (ignore if text like city names)

BAD Examples (DO NOT extract these as capabilities):
❌ "Located at Parakuo Estates on the Abokobi road, Accra, Ghana"
❌ "Near the main hospital"
❌ "In the city center"

GOOD Examples (DO extract these as capabilities):
✓ "24/7 Emergency services"
✓ "Outpatient consultation"
✓ "Laboratory services"

Return valid JSON in this exact format:
{{
  "equipment": ["item1", "item2"],
  "procedures": ["proc1", "proc2"],
  "specialties": ["spec1", "spec2"],
  "capabilities": ["cap1", "cap2"],
  "metadata": {{
    "capacity": 50,
    "facility_type": "Hospital",
    "extracted_info": "brief summary"
  }}
}}"""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parse LLM JSON response"""
        try:
            # Try to extract JSON from response
            response = response.strip()
            
            # Find JSON block
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()
            
            data = json.loads(response)
            
            # Filter capabilities to only include actual services
            raw_capabilities = data.get("capabilities", [])
            filtered_capabilities = []
            
            # Keywords that indicate non-service descriptions
            exclude_keywords = [
                'located', 'location', 'address', 'road', 'street', 'avenue',
                'managed by', 'operated by', 'owned by', 'run by',
                'near', 'next to', 'opposite', 'behind', 'front',
                'city', 'town', 'region', 'area', 'zone', 'district',
                'estate', 'compound', 'building', 'house',
                'contact', 'phone', 'email', 'website'
            ]
            
            for cap in raw_capabilities:
                cap_lower = cap.lower()
                # Skip if it contains any exclude keywords
                if any(keyword in cap_lower for keyword in exclude_keywords):
                    continue
                # Skip if it's too long (likely a description, not a capability)
                if len(cap) > 60:
                    continue
                # Skip if it doesn't contain service-related keywords
                service_keywords = [
                    'service', 'care', 'emergency', 'outpatient', 'inpatient',
                    'consultation', 'treatment', 'diagnostic', 'therapy',
                    '24/7', '24-hour', 'ambulance', 'laboratory', 'lab',
                    'pharmacy', 'ward', 'unit', 'department'
                ]
                if any(keyword in cap_lower for keyword in service_keywords):
                    filtered_capabilities.append(cap)
            
            result = {
                "equipment": [{"name": item, "confidence": 0.8} for item in data.get("equipment", [])],
                "procedures": [{"name": item, "confidence": 0.8} for item in data.get("procedures", [])],
                "specialties": [{"name": item, "confidence": 0.8} for item in data.get("specialties", [])],
                "capabilities": [{"name": item, "confidence": 0.8} for item in filtered_capabilities],
                "metadata": data.get("metadata", {})
            }
            
            # Validate capacity is numeric
            if "capacity" in result["metadata"]:
                try:
                    cap = result["metadata"]["capacity"]
                    if isinstance(cap, str) and not cap.isdigit():
                        result["metadata"]["capacity"] = None
                except:
                    result["metadata"]["capacity"] = None
            
            return result
            
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Response was: {response}")
            return self._empty_result()
    
    def _empty_result(self) -> Dict:
        """Return empty extraction result"""
        return {
            "equipment": [],
            "procedures": [],
            "specialties": [],
            "capabilities": [],
            "metadata": {}
        }
