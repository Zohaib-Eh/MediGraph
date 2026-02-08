"""
Intelligent Document Relationship Extractor
Extracts relationships and entities from structured data descriptions using LLM
General-purpose extractor for any domain
"""

import os
import json
from typing import Dict, List, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

class DocumentExtractor:
    """Extract relationships and entities from document descriptions using LLM"""
    
    def __init__(self, model="llama3.2", domain_context: Optional[str] = None):
        """
        Initialize the extractor
        
        Args:
            model: Ollama model to use (default: llama3.2)
            domain_context: Optional domain context (e.g., "healthcare", "education", "retail")
        """
        # Use Ollama - free and runs locally
        self.llm = ChatOllama(
            model=model,
            temperature=0.0,
        )
        self.domain_context = domain_context or "general"
    
    def extract_relationships_from_description(
        self, 
        entity_name: str, 
        description: str, 
        available_entities: Dict[str, List[str]], 
        source_doc: str,
        relationship_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Extract relationships from an entity's description
        
        Args:
            entity_name: Name of the primary entity (e.g., facility, organization, product)
            description: Text description to analyze
            available_entities: Dict of entity_type -> list of entity names
                e.g., {"equipment": ["MRI", "CT Scanner"], "categories": [...]}
            source_doc: Source document identifier
            relationship_types: Optional list of relationship types to extract
                If None, will use domain-appropriate defaults
            
        Returns:
            List of relationship dictionaries with source, target, type, evidence
        """
        if not description or not description.strip():
            return []
        
        return self._extract_relationships_from_text(
            entity_name, 
            description, 
            available_entities, 
            source_doc,
            relationship_types
        )
    
    def extract_entities_from_description(
        self, 
        description: str, 
        entity_types: Optional[List[str]] = None,
        source_doc: str = ""
    ) -> Dict:
        """
        Extract NEW entities mentioned in description that aren't already structured
        
        Args:
            description: Text to extract entities from
            entity_types: Optional list of entity types to extract
                If None, uses domain-appropriate defaults
            source_doc: Source document identifier
            
        Returns:
            Dictionary of entity lists by type
        """
        if not description or not description.strip():
            return {}
        
        # Default entity types based on domain
        if entity_types is None:
            if self.domain_context == "healthcare":
                entity_types = ["equipment", "procedures", "specialties", "services"]
            else:
                entity_types = ["resources", "capabilities", "categories", "services"]
        
        # Build dynamic extraction instructions
        entity_examples = {
            "equipment": "Specific tools, devices, or machinery",
            "procedures": "Processes, operations, or services performed",
            "specialties": "Areas of expertise or focus",
            "services": "Services provided or offered",
            "resources": "Assets, tools, or materials available",
            "capabilities": "Skills, abilities, or competencies",
            "categories": "Classifications or types",
            "products": "Items, goods, or products"
        }
        
        extraction_list = "\n".join([
            f"{i+1}. {etype.upper()}: {entity_examples.get(etype, 'Items of this type')}"
            for i, etype in enumerate(entity_types)
        ])
        
        json_template = "{{\n" + ",\n".join([
            f'    "{etype}": []'
            for etype in entity_types
        ]) + "\n}}"
        
        prompt = f"""Extract ONLY explicitly mentioned entities from this description.

DESCRIPTION: {description}

Extract:
{extraction_list}

Return ONLY valid JSON - no markdown, no explanation:
{json_template}

IMPORTANT: Extract only what's explicitly mentioned. Return empty arrays if nothing found."""

        messages = [
            SystemMessage(content="You are an entity extractor. Return ONLY valid JSON, no markdown."),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()
            
            # Clean up markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            
            # Ensure all expected keys exist
            for key in entity_types:
                if key not in result:
                    result[key] = []
            
            return result
        
        except Exception as e:
            print(f"Entity extraction error: {e}")
            return {etype: [] for etype in entity_types}
    
    def _extract_relationships_from_text(
        self, 
        entity_name: str, 
        text: str, 
        available_entities: Dict[str, List[str]], 
        source_doc: str,
        relationship_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """Extract relationships from text description"""
        
        # Default relationship types based on domain
        if relationship_types is None:
            if self.domain_context == "healthcare":
                relationship_types = [
                    "HAS - entity has/possesses this resource",
                    "LACKS - entity needs/missing this resource (gap analysis)",
                    "OFFERS - entity provides this service/specialty",
                    "PERFORMS - entity executes this procedure/process",
                    "LOCATED_IN - entity is located in this place"
                ]
            else:
                relationship_types = [
                    "HAS - entity possesses or owns",
                    "LACKS - entity needs or is missing",
                    "PROVIDES - entity offers or supplies",
                    "USES - entity utilizes or employs",
                    "LOCATED_IN - entity is situated in"
                ]
        
        # Format available entities
        entity_list = "\n".join([
            f"- {etype}: {entities[:20]}" + ("..." if len(entities) > 20 else "")
            for etype, entities in available_entities.items()
            if entities
        ])
        
        # Format relationship types
        rel_types_formatted = "\n".join([
            f"{i+1}. {rtype}" for i, rtype in enumerate(relationship_types)
        ])
        
        prompt = f"""Analyze this description and identify relationships between the entity and other entities.

ENTITY: {entity_name}

DESCRIPTION: {text}

AVAILABLE ENTITIES:
{entity_list}

Identify relationships:
{rel_types_formatted}

Return ONLY valid JSON - no markdown, no explanation:
{{
    "relationships": [
        {{
            "source": "{entity_name}",
            "target": "ExactEntityName",
            "type": "HAS",
            "evidence": "quoted text from description"
        }}
    ]
}}

CRITICAL: 
- Pay attention to LACKS/MISSING/NEEDS relationships for gap analysis
- Extract ONLY relationships explicitly mentioned in the description
- Use EXACT entity names from the AVAILABLE ENTITIES list
- Include evidence/justification from the text
- Return empty array if no relationships found"""

        messages = [
            SystemMessage(content="You are a relationship extractor. Return ONLY valid JSON."),
            HumanMessage(content=prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            content = response.content.strip()
            
            # Clean markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            relationships = result.get('relationships', [])
            
            # Add metadata
            for rel in relationships:
                rel['source_document'] = source_doc
                rel['confidence'] = 0.85
                # Ensure source is the entity
                rel['source'] = entity_name
            
            return relationships
        
        except Exception as e:
            print(f"Relationship extraction error: {e}")
            return []
