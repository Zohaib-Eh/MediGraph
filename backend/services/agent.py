"""
Query Agent Service
Handles intelligent querying of the knowledge graph
"""

import os
import json
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

class QueryAgent:
    """Intelligent query agent for medical knowledge graph"""
    
    def __init__(self, graph_service, model="llama3.2"):
        self.graph = graph_service
        # Use Ollama - free and runs locally
        self.llm = ChatOllama(
            model=model,
            temperature=0.0,
        )
    
    def run_query(self, query: str, show_trace: bool = True) -> dict:
        """
        Process user query and return answer
        
        Returns:
            {
                'answer': str,
                'trace': dict (if show_trace),
                'citations': list
            }
        """
        # Step 1: Plan
        plan = self._plan_query(query)
        
        # Step 1.5: Enhance plan with keyword-based queries
        plan = self._enhance_plan_with_keywords(query, plan)
        
        # Step 2: Execute queries
        results = self._execute_plan(plan)
        
        # Step 2.5: For gap queries, add total facility count for comparison
        query_lower = query.lower()
        is_gap_query = any(word in query_lower for word in ['lack', 'missing', 'without', 'need', 'gap', 'prioritize', 'distribute'])
        
        if is_gap_query:
            # Get total facilities and their locations for gap analysis
            all_facilities_query = """
            MATCH (f:Facility)
            OPTIONAL MATCH (f)-[:LOCATED_IN]->(l:Location)
            RETURN f.name as facility, l.city as city, l.region as region
            """
            all_facilities = self.graph.query_custom(all_facilities_query)
            results.append({
                'type': 'all_facilities_for_comparison',
                'data': all_facilities,
                'spec': {'reason': 'Gap analysis needs full facility list for comparison'}
            })
            print(f"📊 Gap query: Added {len(all_facilities)} total facilities for comparison")
        
        # Step 3: Check if we got data, generate suggestions if not
        has_data = any(
            result.get('data') and 
            (isinstance(result['data'], list) and len(result['data']) > 0 or
             isinstance(result['data'], (int, dict)) and result['data'])
            for result in results
        )
        
        suggestions = None
        if not has_data:
            suggestions = self._get_data_suggestions(query)
        
        # Step 4: Synthesize answer
        answer = self._synthesize_answer(query, results, suggestions)
        
        # Extract citations
        citations = self._extract_citations(results)
        
        response = {
            'answer': answer,
            'citations': citations
        }
        
        if show_trace:
            response['trace'] = {
                'plan': plan,
                'queries_executed': len(results),
                'results': results,
                'suggestions': suggestions
            }
        
        return response
    
    def _enhance_plan_with_keywords(self, query: str, plan: dict) -> dict:
        """Dynamically add queries by using LLM to find semantic matches in graph data"""
        enhanced_queries = list(plan.get('queries', []))
        
        # If plan already has queries, let the LLM handle it
        if len(enhanced_queries) > 0:
            return plan
        
        # Only enhance if LLM planner missed something obvious
        # Get schema with samples
        schema = self._get_graph_schema()
        samples = self._get_sample_data(schema)
        
        # Let LLM analyze if query keywords match any relationship data
        analysis_prompt = f"""Given this query: "{query}"

Available relationships with sample data:
{json.dumps(samples, indent=2)}

Does the query semantically relate to ANY of these relationships?
Consider:
- Direct keyword matches
- Semantic similarity (e.g., "capacity" relates to "staff" or "hours")
- Intent understanding (e.g., "expansion needs" relates to "equipment" and "capability")

Return JSON array of relationship types that are relevant:
{{"relevant_relationships": ["REL_TYPE_1", "REL_TYPE_2"]}}

Return empty array if no clear matches."""

        try:
            messages = [
                SystemMessage(content="You are a semantic matcher. Return only valid JSON."),
                HumanMessage(content=analysis_prompt)
            ]
            
            response = self.llm.invoke(messages)
            content = response.content
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            result = json.loads(content.strip())
            relevant_rels = result.get("relevant_relationships", [])
            
            # Add queries for relevant relationships
            for rel_type in relevant_rels:
                if rel_type in samples:
                    sample_info = samples[rel_type]
                    query_spec = {
                        'type': 'find_related',
                        'node_type': sample_info.get('target_type'),
                        'relationship': rel_type,
                        'reason': f'LLM identified {rel_type} as semantically relevant to query'
                    }
                    
                    if not any(q.get('relationship') == rel_type for q in enhanced_queries):
                        enhanced_queries.append(query_spec)
                        print(f"✨ LLM enhanced plan: Added {rel_type}")
        
        except Exception as e:
            print(f"LLM enhancement failed: {e}, using original plan")
        
        plan['queries'] = enhanced_queries
        return plan
    
    def _plan_query(self, query: str) -> dict:
        """Plan how to answer the query using template-based approach"""
        
        query_lower = query.lower()
        
        # Get schema dynamically
        schema = self._get_graph_schema()
        samples = self._get_sample_data(schema)
        
        # Step 1: Identify query pattern (what type of question is this?)
        query_pattern = self._identify_query_pattern(query_lower)
        
        # Step 2: Use LLM only to extract entities/filters (simple task)
        entities = self._extract_entities_from_query(query, samples)
        
        # Step 3: Build plan from template (deterministic)
        plan = self._build_plan_from_template(query_pattern, entities, samples)
        
        print(f"✅ Pattern: {query_pattern}, Entities: {entities}")
        return plan
    
    def _identify_query_pattern(self, query_lower: str) -> str:
        """Identify the type of question - simple pattern matching"""
        
        # Count/aggregate questions
        if any(word in query_lower for word in ['how many', 'count', 'total', 'number of']):
            return 'COUNT'
        
        # List/show questions
        if any(word in query_lower for word in ['what', 'which', 'show', 'list', 'display', 'tell me about']):
            return 'LIST'
        
        # Location/grouping questions
        if any(word in query_lower for word in ['by location', 'by region', 'by city', 'in each', 'per location']):
            return 'GROUP_BY_LOCATION'
        
        # Gap/missing analysis
        if any(word in query_lower for word in ['lack', 'missing', 'without', 'don\'t have', 'need', 'gap']):
            return 'GAP_ANALYSIS'
        
        # Default: list query
        return 'LIST'
    
    def _get_csv_schema_mapping(self) -> dict:
        """Return known CSV schema mappings - this is our contract"""
        return {
            # Known list fields from CSV that become relationships
            'facilities': {'node_type': 'Facility', 'relationship': None},
            'specialties': {'node_type': 'Specialty', 'relationship': 'PROVIDES_SPECIALTY'},
            'procedure': {'node_type': 'Procedure', 'relationship': 'OFFERS_PROCEDURE'},
            'equipment': {'node_type': 'Equipment', 'relationship': 'HAS_EQUIPMENT'},
            'capability': {'node_type': 'Capability', 'relationship': 'HAS_CAPABILITY'},
            
            # Location fields
            'location': {'node_type': 'Location', 'relationship': 'LOCATED_IN'},
            'address': {'node_type': 'Location', 'relationship': 'LOCATED_IN'},
            'city': {'node_type': 'Location', 'relationship': 'LOCATED_IN'},
            'region': {'node_type': 'Location', 'relationship': 'LOCATED_IN'},
            
            # Contact fields
            'phone': {'node_type': 'Contact', 'relationship': 'HAS_CONTACT'},
            'email': {'node_type': 'Contact', 'relationship': 'HAS_CONTACT'},
            'contact': {'node_type': 'Contact', 'relationship': 'HAS_CONTACT'},
            
            # Management/operational
            'operator': {'node_type': 'Operator', 'relationship': 'MANAGED_BY'},
            'managed': {'node_type': 'Operator', 'relationship': 'MANAGED_BY'},
            
            # Temporal
            'established': {'node_type': 'TemporalInfo', 'relationship': 'ESTABLISHED_ON'},
            'founded': {'node_type': 'TemporalInfo', 'relationship': 'ESTABLISHED_ON'},
            'year': {'node_type': 'TemporalInfo', 'relationship': 'ESTABLISHED_ON'},
            
            # Staffing
            'staff': {'node_type': 'StaffingInfo', 'relationship': 'HAS_STAFFING'},
            'employee': {'node_type': 'StaffingInfo', 'relationship': 'HAS_STAFFING'},
            'doctor': {'node_type': 'StaffingInfo', 'relationship': 'HAS_STAFFING'},
            'capacity': {'node_type': 'StaffingInfo', 'relationship': 'HAS_STAFFING'},
        }
    
    def _extract_entities_from_query(self, query: str, samples: dict) -> dict:
        """Use LLM to identify what the user is asking about from CSV schema"""
        
        schema_mapping = self._get_csv_schema_mapping()
        
        # Build options for LLM to choose from
        options = []
        for keyword, mapping in schema_mapping.items():
            if mapping['relationship']:  # Only include items with relationships
                options.append({
                    'keyword': keyword,
                    'relationship': mapping['relationship'],
                    'node_type': mapping['node_type']
                })
        
        # Use LLM to pick the best match
        prompt = f"""Query: "{query}"

What is the user asking about? Pick ONE from this list:
{json.dumps(options, indent=2)}

Rules:
- If asking about procedures/services/operations → pick "procedure"
- If asking about specialties/departments/areas → pick "specialties"
- If asking about equipment/devices/tools → pick "equipment"
- If asking about capabilities/features → pick "capability"
- If asking about location/address/city → pick "location"

Return ONLY the keyword as plain text, nothing else."""

        try:
            messages = [
                SystemMessage(content="Pick the best keyword. Return ONLY the keyword, nothing else."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            picked_keyword = response.content.strip().lower().replace('"', '').replace("'", "")
            
            # Find the mapping for this keyword
            for keyword, mapping in schema_mapping.items():
                if keyword in picked_keyword or picked_keyword in keyword:
                    # Check if this relationship exists in samples
                    for rel_type, sample_info in samples.items():
                        if mapping['relationship'] and mapping['relationship'] in rel_type:
                            return {
                                'relationship': rel_type,
                                'target_type': sample_info.get('target_type', mapping['node_type']),
                                'keyword': None
                            }
                    
                    # Return even if not in samples
                    return {
                        'relationship': mapping['relationship'],
                        'target_type': mapping['node_type'],
                        'keyword': None
                    }
            
        except Exception as e:
            print(f"⚠️  LLM entity extraction failed: {e}")
        
        # Fallback
        return {'relationship': None, 'target_type': 'Facility', 'keyword': None}
    
    def _extract_filter_keyword(self, query_lower: str, examples: list) -> str:
        """Extract filter keyword from query based on examples"""
        # Look for specific terms in the query that match example data
        for example in examples:
            example_lower = str(example).lower()
            # Check for common keywords
            for word in query_lower.split():
                if len(word) > 3 and word in example_lower:
                    return word
        return None
    
    def _llm_extract_entities(self, query: str, samples: dict) -> dict:
        """Fallback: Use LLM to extract entities when schema doesn't match"""
        
        # Build list of available entity types from samples
        available = []
        for rel_type, info in samples.items():
            available.append({
                'relationship': rel_type,
                'target_type': info.get('target_type'),
                'examples': info.get('examples', [])[:3]
            })
        
        prompt = f"""Query: "{query}"

Available data types:
{json.dumps(available, indent=2)}

What is the user asking about? Return ONE item from the list above.

Output JSON ONLY:
{{"relationship": "exact relationship name from list", "target_type": "exact type from list", "keyword": "search keyword if any or null"}}

Examples:
"What procedures?" → {{"relationship": "OFFERS_PROCEDURE", "target_type": "Procedure", "keyword": null}}
"Show ultrasound equipment" → {{"relationship": "OFFERS_PROCEDURE", "target_type": "Procedure", "keyword": "ultrasound"}}
"24/7 services" → {{"relationship": "HAS_CAPABILITY", "target_type": "Capability", "keyword": "24"}}"""

        try:
            messages = [
                SystemMessage(content="Extract entities. Return ONLY valid JSON."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            content = response.content.strip()
            
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            if not content.startswith('{'):
                start = content.find('{')
                if start != -1:
                    content = content[start:]
            
            return json.loads(content)
            
        except Exception as e:
            print(f"⚠️  Entity extraction failed: {e}")
            # Fallback: use first available relationship
            if samples:
                first_rel = list(samples.keys())[0]
                return {
                    'relationship': first_rel,
                    'target_type': samples[first_rel].get('target_type'),
                    'keyword': None
                }
            return {'relationship': None, 'target_type': 'Facility', 'keyword': None}
    
    def _build_plan_from_template(self, pattern: str, entities: dict, samples: dict) -> dict:
        """Build query plan from template - deterministic, no LLM needed"""
        
        rel = entities.get('relationship')
        node_type = entities.get('target_type', 'Facility')
        keyword = entities.get('keyword')
        
        if pattern == 'COUNT':
            return {
                'approach': f"Count {node_type} entities",
                'queries': [{
                    'type': 'count_nodes',
                    'node_type': node_type,
                    'reason': f'Counting {node_type}'
                }]
            }
        
        elif pattern == 'GROUP_BY_LOCATION':
            return {
                'approach': 'Group facilities by location',
                'queries': [{
                    'type': 'location_analysis',
                    'reason': 'Location grouping'
                }]
            }
        
        elif pattern == 'LIST' or pattern == 'GAP_ANALYSIS':
            query_spec = {
                'type': 'find_related',
                'node_type': node_type,
                'reason': f'Finding {node_type}'
            }
            
            # Add relationship if we have it
            if rel:
                query_spec['relationship'] = rel
            
            # Add filter keyword if we have it
            if keyword:
                query_spec['filter'] = keyword
            
            return {
                'approach': f"List {node_type} with {rel or 'relationships'}",
                'queries': [query_spec]
            }
        
        # Fallback
        return {
            'approach': 'General query',
            'queries': [{
                'type': 'location_analysis',
                'reason': 'Fallback analysis'
            }]
        }
    
    def _get_graph_schema(self) -> dict:
        """Get available node labels and relationship types from graph"""
        try:
            # Get all node labels
            labels_query = "CALL db.labels()"
            labels_result = self.graph.query_custom(labels_query)
            node_labels = [r['label'] for r in labels_result] if labels_result else []
            
            # Get all relationship types
            rels_query = "CALL db.relationshipTypes()"
            rels_result = self.graph.query_custom(rels_query)
            relationship_types = [r['relationshipType'] for r in rels_result] if rels_result else []
            
            return {
                "node_labels": node_labels,
                "relationship_types": relationship_types
            }
        except Exception as e:
            print(f"Schema introspection failed: {e}")
            # Return common types as fallback
            return {
                "node_labels": ["Facility", "Equipment", "Procedure", "Specialty", "Capability", "Location"],
                "relationship_types": ["HAS_EQUIPMENT", "OFFERS_PROCEDURE", "PROVIDES_SPECIALTY", "HAS_CAPABILITY", "LOCATED_IN"]
            }
    
    def _get_sample_data(self, schema: dict) -> dict:
        """Get sample data for each relationship to help query planner"""
        samples = {}
        
        for rel_type in schema['relationship_types'][:10]:  # Limit to avoid too much data
            try:
                sample_query = f"""
                MATCH (f:Facility)-[r:{rel_type}]->(n)
                RETURN type(r) as relationship, 
                       labels(n)[0] as target_type,
                       collect(distinct n.name)[0..5] as examples
                LIMIT 1
                """
                result = self.graph.query_custom(sample_query)
                if result and result[0].get('examples'):
                    samples[rel_type] = {
                        'target_type': result[0].get('target_type'),
                        'examples': result[0].get('examples')
                    }
            except Exception as e:
                print(f"Error sampling {rel_type}: {e}")
                continue
        
        return samples
    
    def _execute_plan(self, plan: dict) -> list:
        """Execute planned queries dynamically with data validation"""
        results = []
        
        for query_spec in plan.get("queries", []):
            query_type = query_spec.get("type", "")
            
            try:
                # Dynamic query execution based on type
                if query_type == "count_nodes":
                    node_type = query_spec.get("node_type", "Facility")
                    result = self._count_nodes(node_type)
                    results.append({
                        "type": query_type,
                        "data": result,
                        "spec": query_spec
                    })
                    
                elif query_type == "find_related":
                    # First check if this relationship actually has data
                    relationship = query_spec.get("relationship")
                    if relationship:
                        count_query = f"MATCH ()-[r:{relationship}]->() RETURN count(r) as count"
                        count_result = self.graph.query_custom(count_query)
                        rel_count = count_result[0]['count'] if count_result else 0
                        
                        if rel_count == 0:
                            # Relationship exists in schema but has no data
                            results.append({
                                "type": query_type,
                                "data": [],
                                "spec": query_spec,
                                "warning": f"Relationship {relationship} exists but contains no data. This field may be empty in the uploaded CSV."
                            })
                            print(f"⚠️  {relationship} has no data (likely empty in CSV)")
                            continue
                    
                    result = self._find_related(query_spec)
                    results.append({
                        "type": query_type,
                        "data": result,
                        "spec": query_spec
                    })
                    
                elif query_type == "location_analysis":
                    result = self._analyze_locations()
                    results.append({
                        "type": query_type,
                        "data": result,
                        "spec": query_spec
                    })
                    
                elif query_type == "custom_cypher":
                    cypher = query_spec.get("cypher", "")
                    result = self.graph.query_custom(cypher)
                    results.append({
                        "type": query_type,
                        "data": result,
                        "spec": query_spec
                    })
                else:
                    print(f"Unknown query type: {query_type}")
                    
            except Exception as e:
                print(f"Error executing {query_type}: {e}")
                results.append({
                    "type": query_type,
                    "error": str(e),
                    "spec": query_spec
                })
        
        return results
    
    def _count_nodes(self, node_type: str) -> int:
        """Count nodes of any type"""
        query = f"MATCH (n:{node_type}) RETURN count(n) as count"
        result = self.graph.query_custom(query)
        return result[0]['count'] if result else 0
    
    def _find_related(self, query_spec: dict) -> list:
        """Find nodes related to facilities via any relationship"""
        node_type = query_spec.get("node_type", "Facility")
        relationship = query_spec.get("relationship", "")
        filter_text = query_spec.get("filter", "")
        
        if relationship:
            # Specific relationship query
            query = f"""
            MATCH (f:Facility)-[r:{relationship}]->(n:{node_type})
            OPTIONAL MATCH (f)-[:LOCATED_IN]->(l:Location)
            RETURN f.name as facility, n.name as item, l.city as city, l.region as region
            """
            
            # Apply filter if provided
            if filter_text:
                # Add WHERE clause for filtering
                filter_conditions = []
                for term in filter_text.split(" OR "):
                    term = term.strip()
                    filter_conditions.append(f"n.name =~ '(?i).*{term}.*'")
                
                query = query.replace("RETURN", f"WHERE {' OR '.join(filter_conditions)}\nRETURN")
            
            print(f"🔍 Executing Cypher: {query[:200]}...")
        else:
            # Just list nodes of this type
            query = f"""
            MATCH (n:{node_type})
            RETURN n.name as item
            """
        
        result = self.graph.query_custom(query)
        print(f"📊 Query returned {len(result) if result else 0} results")
        return result
    
    def _list_facilities(self, criteria: str = None) -> list:
        """List facilities with optional criteria"""
        if criteria and "city:" in criteria:
            city = criteria.split("city:")[1].strip()
            query = """
                MATCH (f:Facility)-[:LOCATED_IN]->(l:Location)
                WHERE l.city = $city
                RETURN f.name as name, l.city as city
                LIMIT 20
            """
            return self.graph.query_custom(query, {"city": city})
        else:
            query = """
                MATCH (f:Facility)
                OPTIONAL MATCH (f)-[:LOCATED_IN]->(l:Location)
                RETURN f.name as name, l.city as city
                LIMIT 20
            """
            return self.graph.query_custom(query)
    
    def _find_equipment(self, criteria: str = None) -> list:
        """Find equipment at facilities"""
        if criteria and "city:" in criteria:
            city = criteria.split("city:")[1].strip()
            query = """
                MATCH (f:Facility)-[:LOCATED_IN]->(l:Location)
                WHERE l.city = $city
                MATCH (f)-[:HAS_EQUIPMENT]->(e:Equipment)
                RETURN f.name as facility, e.name as equipment, l.city as city
                LIMIT 50
            """
            return self.graph.query_custom(query, {"city": city})
        else:
            query = """
                MATCH (f:Facility)-[:HAS_EQUIPMENT]->(e:Equipment)
                RETURN f.name as facility, e.name as equipment
                LIMIT 50
            """
            return self.graph.query_custom(query)
    
    def _find_specialties(self, criteria: str = None) -> list:
        """Find specialties at facilities"""
        query = """
            MATCH (f:Facility)-[:PROVIDES_SPECIALTY]->(s:Specialty)
            RETURN f.name as facility, s.name as specialty
            LIMIT 50
        """
        return self.graph.query_custom(query)
    
    def _find_procedures(self, criteria: str = None) -> list:
        """Find procedures offered by facilities"""
        if criteria and "city:" in criteria:
            city = criteria.split("city:")[1].strip()
            query = """
                MATCH (f:Facility)-[:LOCATED_IN]->(l:Location)
                WHERE l.city = $city
                MATCH (f)-[:OFFERS_PROCEDURE]->(p:Procedure)
                RETURN f.name as facility, p.name as procedure, l.city as city
                LIMIT 50
            """
            return self.graph.query_custom(query, {"city": city})
        else:
            query = """
                MATCH (f:Facility)-[:OFFERS_PROCEDURE]->(p:Procedure)
                OPTIONAL MATCH (f)-[:LOCATED_IN]->(l:Location)
                RETURN f.name as facility, p.name as procedure, l.city as city
                LIMIT 50
            """
            return self.graph.query_custom(query)
    
    def _find_capabilities(self, criteria: str = None) -> list:
        """Find service capabilities at facilities"""
        if criteria and "24" in criteria.lower():
            # Filter for 24/7 services
            query = """
                MATCH (f:Facility)-[:HAS_CAPABILITY]->(c:Capability)
                WHERE c.name =~ '(?i).*24.*' OR c.name =~ '(?i).*always open.*'
                OPTIONAL MATCH (f)-[:LOCATED_IN]->(l:Location)
                RETURN f.name as facility, c.name as capability, l.city as city
                LIMIT 50
            """
            return self.graph.query_custom(query)
        else:
            query = """
                MATCH (f:Facility)-[:HAS_CAPABILITY]->(c:Capability)
                OPTIONAL MATCH (f)-[:LOCATED_IN]->(l:Location)
                RETURN f.name as facility, c.name as capability, l.city as city
                LIMIT 50
            """
            return self.graph.query_custom(query)
    
    def _analyze_locations(self, criteria: str = None) -> list:
        """Analyze facilities by location"""
        query = """
            MATCH (l:Location)<-[:LOCATED_IN]-(f:Facility)
            RETURN l.city as city, count(f) as facility_count
            ORDER BY facility_count DESC
        """
        return self.graph.query_custom(query)
    
    def _synthesize_answer(self, query: str, results: list, suggestions: dict = None) -> str:
        """Synthesize final answer from results, with helpful suggestions if no data"""
        
        # Check if we have any meaningful data
        has_data = any(
            result.get('data') and 
            (isinstance(result['data'], list) and len(result['data']) > 0 or
             isinstance(result['data'], (int, dict)) and result['data'])
            for result in results
        )
        
        # Check if we have warnings about empty CSV fields
        warnings = [r.get('warning') for r in results if r.get('warning')]
        
        if warnings and not has_data:
            # Data exists in schema but is empty in CSV
            warning_text = "\n".join([f"- {w}" for w in warnings])
            
            return f"""**Direct Answer:**

The data you're asking about exists in the system's schema but appears to be empty in the uploaded CSV file.

**What This Means:**

The CSV file likely has these columns, but they contain no values (empty/null). Specifically:

{warning_text}

**What You Can Do:**

1. **Check your CSV file** - Ensure these columns have actual data filled in
2. **Re-upload the CSV** with populated data for these fields
3. **Try alternative queries** - Ask about fields that do have data

**Available Data:**

To see what data IS available, try the debug endpoint: http://localhost:8000/debug/schema"""
        
        if not has_data and suggestions:
            # Build a helpful response showing what IS available
            available_items = suggestions.get('available_relationships', {})
            
            if not available_items:
                return """**Direct Answer:**
I don't have any data in the knowledge graph yet. Please upload a CSV file to populate the system.

**Next Steps:**
1. Upload your healthcare facility data via the Data Management tab
2. The system will automatically extract entities and relationships
3. Then you can query the knowledge graph for insights"""
            
            available_text = []
            suggested_queries = []
            
            for rel_type, info in available_items.items():
                # Format relationship name nicely
                rel_name = rel_type.replace('_', ' ').title()
                examples = info['examples'][:2]
                
                available_text.append(
                    f"**{rel_name}**: {info['count']} items\n  Examples: {', '.join(examples)}"
                )
                
                # Generate smart query suggestions based on relationship type
                target_type = info['target_type']
                if 'PROCEDURE' in rel_type:
                    suggested_queries.append("What procedures do facilities offer?")
                elif 'CAPABILITY' in rel_type:
                    suggested_queries.append("Which facilities provide 24/7 services?")
                elif 'SPECIALTY' in rel_type:
                    suggested_queries.append("List facilities by specialty")
                elif 'EQUIPMENT' in rel_type:
                    suggested_queries.append("What equipment is available?")
                elif 'STAFF' in rel_type or 'EMPLOYEE' in rel_type:
                    suggested_queries.append("Show staffing levels across facilities")
                elif 'LOCATION' in rel_type:
                    suggested_queries.append("Analyze facilities by region")
                elif 'CONTACT' in rel_type:
                    suggested_queries.append("Get contact information for facilities")
                else:
                    suggested_queries.append(f"Show me {target_type.lower()}s")
            
            # Add explanation of how available data relates to query
            query_lower = query.lower()
            relevance_note = ""
            if 'capacity' in query_lower or 'utilization' in query_lower:
                relevance_note = "\n\n💡 **Note:** While we don't have direct utilization metrics, staffing levels and operating hours can indicate facility capacity."
            elif 'expansion' in query_lower:
                relevance_note = "\n\n💡 **Note:** Expansion needs can be inferred from staffing levels, service offerings, and equipment availability."
            elif 'busy' in query_lower or 'crowded' in query_lower:
                relevance_note = "\n\n💡 **Note:** Facility workload can be estimated from staffing data and hours of operation."
            
            available_formatted = "\n\n".join(available_text)
            queries_formatted = "\n".join([f"{i+1}. \"{q}\"" for i, q in enumerate(list(dict.fromkeys(suggested_queries))[:4])])
            
            prompt = f"""The user asked: "{query}"

We don't have specific data for this query, but here's what's available:

{available_formatted}{relevance_note}

Based on this, suggest the user try these queries instead:
{queries_formatted}

Please format as:
**Direct Answer:**
[Polite explanation + mention what related data we DO have]

**Available Data:**
[List the relationship types with counts and examples, PLUS explain how they relate to the query]

**Try Asking:**
[List the suggested queries]"""
            
            messages = [
                SystemMessage(content="You are a helpful assistant. Be concise and suggest alternatives."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            return response.content
        
        # Normal path - we have data
        # Extract actual data sources (facility names, locations)
        sources = self._extract_data_sources(results)
        sources_text = "\n".join([f"- {s}" for s in sources]) if sources else "No specific facilities found in results."
        
        # Detect if this is a "lack/missing/gap" query
        query_lower = query.lower()
        is_gap_query = any(word in query_lower for word in ['lack', 'missing', 'without', 'don\'t have', 'need', 'gap', 'prioritize', 'distribute'])
        
        # Detect equipment inference queries
        equipment_keywords = ['equipment', 'machine', 'device', 'tool', 'technology']
        is_equipment_query = any(word in query_lower for word in equipment_keywords)
        
        gap_instructions = ""
        if is_gap_query:
            gap_instructions = """
CRITICAL - This is a GAP ANALYSIS query:
- The data shows facilities that HAVE the capability/equipment/service
- You must INFER which facilities DON'T have it by exclusion
- Compare ALL facilities in the graph vs those that HAVE the item
- Analyze geographic gaps (which regions have coverage, which don't)
- Prioritize recommendations based on population centers without coverage
"""
        
        if is_equipment_query:
            gap_instructions += """
CRITICAL - Equipment INFERENCE Logic:
- If a facility OFFERS a procedure (e.g., "performs ultrasound scans"), they HAVE the equipment (ultrasound machine)
- If a facility offers "ECG", they HAVE ECG equipment
- If a facility offers "X-ray imaging", they HAVE X-ray equipment
- PROCEDURE data is PROXY for EQUIPMENT ownership
- State clearly: "Facilities offering X procedure have X equipment"
- Then identify which facilities DON'T offer that procedure = they LACK the equipment
"""
        
        prompt = f"""Synthesize an answer to the user's query based on ONLY the data provided.

QUERY: {query}

DATA FROM KNOWLEDGE GRAPH:
{json.dumps(results, indent=2)}

SOURCES (Facilities in the knowledge graph):
{sources_text}
{gap_instructions}

Instructions:
1. Provide a direct answer to the query using ONLY the data above
2. Include key findings with specific numbers from the data
3. Provide actionable recommendations based on the findings
4. In the Sources section, list ONLY the facilities mentioned in the data above
5. DO NOT mention external sources like "Ghana Health Service" or other organizations not in the data
6. DO NOT say "no specific sources available" - use the facility names from the data
7. SMART INTERPRETATION: 
   - If user asks "which facilities LACK X", analyze the data to find facilities WITHOUT X
   - If user asks about equipment distribution, consider procedure data as proxy for equipment
   - For "ultrasound equipment", facilities offering "ultrasound scans" likely HAVE the equipment
8. FORMAT CAREFULLY: 
   - Use clean markdown with proper spacing
   - Put blank lines between sections
   - Use bullet points for clarity
   - Keep it professional and readable

Format your response EXACTLY like this (with blank lines between sections):

**Direct Answer:**

[Provide a clear, concise 2-3 sentence answer to the main question]

**Key Findings:**

- **Finding 1:** [Specific data point with numbers]
- **Finding 2:** [Specific data point with numbers]  
- **Finding 3:** [Specific data point with numbers]

**Actionable Recommendations:**

1. **Priority Action:** [Strategic recommendation with specific targets]
2. **Secondary Action:** [Follow-up recommendation]
3. **Long-term Strategy:** [Broader strategic guidance]

**Sources:**

The following facilities from the knowledge graph were analyzed:
- [Facility Name] ([Location])
- [Facility Name] ([Location])
- [Facility Name] ([Location])"""

        messages = [
            SystemMessage(content="You are a medical intelligence analyst. Use ONLY the provided data. Do not hallucinate external sources."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    def _extract_data_sources(self, results: list) -> list:
        """Extract facility names and locations from query results as sources"""
        sources = []
        
        for result in results:
            data = result.get('data', [])
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        # Extract facility name with location if available
                        facility = item.get('facility') or item.get('name')
                        location = item.get('city') or item.get('location')
                        
                        if facility:
                            if location:
                                sources.append(f"{facility} ({location})")
                            else:
                                sources.append(facility)
        
        # Deduplicate while preserving order
        seen = set()
        unique_sources = []
        for source in sources:
            if source not in seen:
                seen.add(source)
                unique_sources.append(source)
        
        return unique_sources
    
    def _extract_citations(self, results: list) -> list:
        """Extract facility names as citations from results"""
        return self._extract_data_sources(results)
    
    def _get_data_suggestions(self, original_query: str) -> dict:
        """When query returns no data, suggest what IS available"""
        try:
            schema = self._get_graph_schema()
            
            # Get sample counts for each relationship type
            available_data = {}
            
            for rel_type in schema['relationship_types']:
                try:
                    count_query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
                    result = self.graph.query_custom(count_query)
                    count = result[0]['count'] if result else 0
                    
                    if count > 0:
                        # Get sample data
                        sample_query = f"""
                        MATCH (f:Facility)-[r:{rel_type}]->(n)
                        RETURN type(r) as relationship, 
                               labels(n)[0] as target_type, 
                               count(*) as count,
                               collect(distinct n.name)[0..3] as examples
                        LIMIT 1
                        """
                        sample = self.graph.query_custom(sample_query)
                        if sample:
                            available_data[rel_type] = {
                                'count': count,
                                'target_type': sample[0].get('target_type'),
                                'examples': sample[0].get('examples', [])
                            }
                except Exception as e:
                    print(f"Error checking {rel_type}: {e}")
                    continue
            
            return {
                'available_relationships': available_data,
                'original_query': original_query,
                'node_types': schema['node_labels']
            }
            
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return {}