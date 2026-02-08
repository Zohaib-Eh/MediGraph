"""
Neo4j Graph Service
Handles all knowledge graph operations
"""

import os
import math
from neo4j import GraphDatabase
from typing import List, Dict, Any

class GraphService:
    """Neo4j knowledge graph operations"""
    
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "password")
        
        self.driver = GraphDatabase.driver(
            uri, 
            auth=(user, password),
            max_connection_lifetime=3600,  # 1 hour
            max_connection_pool_size=50,
            connection_acquisition_timeout=60
        )
        self._init_constraints()
    
    def close(self):
        """Close the driver connection"""
        if self.driver:
            self.driver.close()
    
    def _sanitize_value(self, value: Any) -> Any:
        """Replace NaN and Inf values with None for JSON serialization"""
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None
        elif isinstance(value, dict):
            return {k: self._sanitize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._sanitize_value(item) for item in value]
        return value
    
    def _init_constraints(self):
        """Create uniqueness constraints"""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (h:Facility) REQUIRE h.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Equipment) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Procedure) REQUIRE p.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Specialty) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.name IS UNIQUE",
        ]
        
        with self.driver.session() as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except:
                    pass
    
    def test_connection(self) -> bool:
        """Test Neo4j connection"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            return True
        except Exception as e:
            print(f"Neo4j connection test failed: {e}")
            return False
    
    def clear_graph(self):
        """Delete all nodes and relationships"""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
    
    def build_graph(self, entities: Dict, relationships: List):
        """Build knowledge graph from entities and relationships (supports dynamic entity types)"""
        
        # Log what we're building
        print("\n🔨 Building Neo4j Graph...")
        print(f"Entities to create:")
        for entity_type, entity_list in entities.items():
            print(f"  {entity_type}: {len(entity_list)}")
        print(f"Relationships to create: {len(relationships)}")
        
        with self.driver.session() as session:
            # Create nodes dynamically for all entity types
            self._create_all_nodes(session, entities)
            # Add facilities
            print(f"\n  Creating {len(entities.get('facilities', []))} Facility nodes...")
            for facility in entities.get('facilities', []):
                try:
                    # Handle metadata as array property
                    metadata = facility.get('metadata', [])
                    session.run("""
                        MERGE (f:Facility {name: $name})
                        SET f.capacity = $capacity,
                            f.type = $facility_type,
                            f.operator_type = $operator_type,
                            f.number_doctors = $number_doctors,
                            f.source_document = $source_document,
                            f.metadata = $metadata
                    """, 
                        name=facility.get('name'),
                        capacity=facility.get('capacity'),
                        facility_type=facility.get('type'),
                        operator_type=facility.get('operator_type'),
                        number_doctors=facility.get('number_doctors'),
                        source_document=facility.get('source_document'),
                        metadata=metadata
                    )
                except Exception as e:
                    print(f"    Error creating facility {facility.get('name')}: {e}")
            
            # Add equipment
            print(f"  Creating {len(entities.get('equipment', []))} Equipment nodes...")
            for equipment in entities.get('equipment', []):
                session.run("""
                    MERGE (e:Equipment {name: $name})
                    SET e.type = $equipment_type,
                        e.status = $status,
                        e.source_document = $source_document
                """, **equipment)
            
            # Add procedures
            print(f"  Creating {len(entities.get('procedures', []))} Procedure nodes...")
            for procedure in entities.get('procedures', []):
                session.run("""
                    MERGE (p:Procedure {name: $name})
                    SET p.category = $category,
                        p.source_document = $source_document
                """, **procedure)
            
            print(f"  Creating {len(entities.get('specialties', []))} Specialty nodes...")
            # Add specialties
            for specialty in entities.get('specialties', []):
                session.run("""
                    MERGE (s:Specialty {name: $name})
                    SET s.type = $type,
                        s.source_document = $source_document
                """, **specialty)
            print(f"  Creating {len(entities.get('locations', []))} Location nodes...")
            
            # Add locations
            for location in entities.get('locations', []):
                session.run("""
                    MERGE (l:Location {name: $name})
                    SET l.city = $city,
                        l.state_or_region = $state_or_region,
                        l.country = $country,
                        l.country_code = $country_code,
                        l.type = $type,
                        l.source_document = $source_document
                """, 
                    name=location.get('name'),
                    city=location.get('city', ''),
                    state_or_region=location.get('state_or_region', ''),
                    country=location.get('country', ''),
                    country_code=location.get('country_code', ''),
                    type=location.get('type', 'location'),
                    source_document=location.get('source_document', '')
                )
            print(f"  Creating {len(entities.get('capabilities', []))} Capability nodes...")
            
            # Add capabilities
            for capability in entities.get('capabilities', []):
                session.run("""
                    MERGE (c:Capability {name: $name})
                    SET c.type = $type,
                        c.source_document = $source_document
                """, **capability)
            
            # Add contacts
            print(f"  Creating {len(entities.get('contacts', []))} Contact nodes...")
            for contact in entities.get('contacts', []):
                session.run("""
                    MERGE (c:Contact {name: $name})
                    SET c.type = $type,
                        c.source_document = $source_document
                """, **contact)
            
            # Add operators
            print(f"  Creating {len(entities.get('operators', []))} Operator nodes...")
            for operator in entities.get('operators', []):
                session.run("""
                    MERGE (o:Operator {name: $name})
                    SET o.type = $type,
                        o.source_document = $source_document
                """, **operator)
            
            # Add temporal info (founding dates, establishment info)
            print(f"  Creating {len(entities.get('temporal_info', []))} TemporalInfo nodes...")
            for temporal in entities.get('temporal_info', []):
                session.run("""
                    MERGE (t:TemporalInfo {name: $name})
                    SET t.type = $type,
                        t.source_document = $source_document
                """, **temporal)
            
            # Add staffing info (employee counts, team size)
            print(f"  Creating {len(entities.get('staffing_info', []))} StaffingInfo nodes...")
            for staffing in entities.get('staffing_info', []):
                session.run("""
                    MERGE (s:StaffingInfo {name: $name})
                    SET s.type = $type,
                        s.source_document = $source_document
                """, **staffing)
            
            print(f"  Creating {len(relationships)} relationships...")
            created_rels = 0
            failed_rels = 0
            
            # Add relationships
            print(f"  Creating {len(relationships)} relationships...")
            created_rels = 0
            failed_rels = 0
            for rel in relationships:
                rel_type = rel['type']
                source_label, target_label = self._infer_labels(rel_type)
                
                query = f"""
                    MATCH (source:{source_label} {{name: $source}})
                    MATCH (target:{target_label} {{name: $target}})
                    MERGE (source)-[r:{rel_type}]->(target)
                    SET r.confidence = $confidence,
                        r.source_document = $source_document,
                        r.evidence = $evidence
                """
                
                try:
                    result = session.run(query,
                        source=rel['source'],
                        target=rel['target'],
                        confidence=rel.get('confidence', 1.0),
                        source_document=rel.get('source_document', ''),
                        evidence=rel.get('evidence', '')
                    )
                    # Check if MATCH actually found nodes
                    summary = result.consume()
                    if summary.counters.relationships_created > 0 or summary.counters.properties_set > 0:
                        created_rels += 1
                    else:
                        failed_rels += 1
                        if failed_rels <= 10:  # Print first 10 failures
                            print(f"    ⚠️  No nodes found: {rel['source']} ({source_label}) -[{rel_type}]-> {rel['target']} ({target_label})")
                except Exception as e:
                    failed_rels += 1
                    if failed_rels <= 10:  # Print first 10 failures
                        print(f"    ❌ Failed relationship: {rel['source']} -[{rel_type}]-> {rel['target']}: {e}")
            
            print(f"  ✓ Created {created_rels} relationships ({failed_rels} failed)\n")
    
    def _create_all_nodes(self, session, entities: Dict):
        """Dynamically create nodes for all entity types"""
        
        # Special handling for facilities (has more properties)
        print(f"\n  Creating {len(entities.get('facilities', []))} Facility nodes...")
        for facility in entities.get('facilities', []):
            try:
                metadata = facility.get('metadata', [])
                session.run("""
                    MERGE (f:Facility {name: $name})
                    SET f.capacity = $capacity,
                        f.type = $facility_type,
                        f.operator_type = $operator_type,
                        f.number_doctors = $number_doctors,
                        f.source_document = $source_document,
                        f.metadata = $metadata
                """, 
                    name=facility.get('name'),
                    capacity=facility.get('capacity'),
                    facility_type=facility.get('type'),
                    operator_type=facility.get('operator_type'),
                    number_doctors=facility.get('number_doctors'),
                    source_document=facility.get('source_document'),
                    metadata=metadata
                )
            except Exception as e:
                print(f"    Error creating facility {facility.get('name')}: {e}")
        
        # Special handling for locations (has city, country, etc.)
        print(f"  Creating {len(entities.get('locations', []))} Location nodes...")
        for location in entities.get('locations', []):
            session.run("""
                MERGE (l:Location {name: $name})
                SET l.city = $city,
                    l.state_or_region = $state_or_region,
                    l.country = $country,
                    l.country_code = $country_code,
                    l.type = $type,
                    l.source_document = $source_document
            """, 
                name=location.get('name'),
                city=location.get('city', ''),
                state_or_region=location.get('state_or_region', ''),
                country=location.get('country', ''),
                country_code=location.get('country_code', ''),
                type=location.get('type', 'location'),
                source_document=location.get('source_document', '')
            )
        
        # Generic handling for all other entity types
        for entity_type, entity_list in entities.items():
            if entity_type in ['facilities', 'locations']:
                continue  # Already handled above
            
            if not entity_list:
                continue
            
            # Convert collection name to Neo4j label (PascalCase singular)
            label = self._collection_to_label(entity_type)
            print(f"  Creating {len(entity_list)} {label} nodes...")
            
            for entity in entity_list:
                # Build dynamic property setting
                props = {
                    'name': entity.get('name'),
                    'type': entity.get('type', entity_type),
                    'source_document': entity.get('source_document', '')
                }
                
                # Add any additional properties
                for key, value in entity.items():
                    if key not in ['name', 'type', 'source_document'] and value is not None:
                        props[key] = value
                
                # Build SET clause dynamically
                set_clause = ', '.join([f"n.{key} = ${key}" for key in props.keys()])
                
                query = f"""
                    MERGE (n:{label} {{name: $name}})
                    SET {set_clause}
                """
                
                try:
                    session.run(query, **props)
                except Exception as e:
                    print(f"    Error creating {label} node '{entity.get('name')}': {e}")
    
    def _collection_to_label(self, collection_name: str) -> str:
        """Convert collection name to Neo4j label (snake_case plural -> PascalCase singular)"""
        # Common mappings
        label_map = {
            'facilities': 'Facility',
            'equipment': 'Equipment',
            'procedures': 'Procedure',
            'specialties': 'Specialty',
            'capabilities': 'Capability',
            'locations': 'Location',
            'contacts': 'Contact',
            'operators': 'Operator',
            'temporal_info': 'TemporalInfo',
            'staffing_info': 'StaffingInfo',
        }
        
        if collection_name in label_map:
            return label_map[collection_name]
        
        # Dynamic conversion: snake_case_plural -> PascalCase
        import re
        # Remove trailing 's' for plurals
        singular = collection_name.rstrip('s') if collection_name.endswith('s') else collection_name
        # snake_case -> PascalCase
        words = singular.split('_')
        return ''.join(word.capitalize() for word in words)
    
    def _infer_labels(self, rel_type: str) -> tuple:
        """Infer node labels from relationship type"""
        label_map = {
            "HAS_EQUIPMENT": ("Facility", "Equipment"),
            "LACKS_EQUIPMENT": ("Facility", "Equipment"),
            "OFFERS_PROCEDURE": ("Facility", "Procedure"),
            "REQUIRES_EQUIPMENT": ("Procedure", "Equipment"),
            "LOCATED_IN": ("Facility", "Location"),
            "PROVIDES_SPECIALTY": ("Facility", "Specialty"),
            "LACKS_SPECIALTY": ("Facility", "Specialty"),
            "HAS_CAPABILITY": ("Facility", "Capability"),
            "HAS_CONTACT": ("Facility", "Contact"),
            "MANAGED_BY": ("Facility", "Operator"),
            "ESTABLISHED_ON": ("Facility", "TemporalInfo"),
            "HAS_STAFFING": ("Facility", "StaffingInfo"),
        }
        return label_map.get(rel_type, ("Facility", "Equipment"))
    
    def get_stats(self) -> Dict:
        """Get graph statistics"""
        stats = {
            'total_facilities': 0,
            'total_equipment': 0,
            'total_procedures': 0,
            'total_specialties': 0,
            'total_locations': 0,
            'total_capabilities': 0,
            'total_relationships': 0
        }
        
        try:
            # Verify connection is alive
            if not self.test_connection():
                print("⚠️  Neo4j connection not available, returning zero stats")
                return stats
            
            with self.driver.session() as session:
                label_map = {
                    'Facility': 'total_facilities',
                    'Equipment': 'total_equipment',
                    'Procedure': 'total_procedures',
                    'Specialty': 'total_specialties',
                    'Location': 'total_locations',
                    'Capability': 'total_capabilities'
                }
                
                for label, key in label_map.items():
                    try:
                        result = session.run(f"MATCH (n:{label}) RETURN COUNT(n) as count")
                        record = result.single()
                        stats[key] = record['count'] if record else 0
                    except Exception as e:
                        print(f"Error getting count for {label}: {e}")
                        stats[key] = 0
                
                try:
                    result = session.run("MATCH ()-[r]->() RETURN COUNT(r) as count")
                    record = result.single()
                    stats['total_relationships'] = record['count'] if record else 0
                except Exception as e:
                    print(f"Error getting relationship count: {e}")
                    stats['total_relationships'] = 0
        except Exception as e:
            print(f"❌ Error getting graph stats: {e}")
            # Return zero stats instead of raising exception
        
        return stats
    
    def find_medical_deserts(self) -> List[Dict]:
        """Find regions with insufficient coverage"""
        query = """
            MATCH (l:Location)
            OPTIONAL MATCH (l)<-[:LOCATED_IN]-(f:Facility)
            WITH l, COUNT(f) as facility_count
            WHERE facility_count < 3
            RETURN l.name as region,
                   l.state_or_region as state,
                   facility_count,
                   l.source_document as source
            ORDER BY facility_count ASC
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def find_equipment_gaps(self) -> List[Dict]:
        """Find facilities lacking equipment"""
        query = """
            MATCH (f:Facility)-[r:LACKS_EQUIPMENT]->(e:Equipment)
            OPTIONAL MATCH (f)-[:LOCATED_IN]->(l:Location)
            WITH f, l, COLLECT({
                equipment: e.name,
                type: e.equipment_type,
                source: r.source_document
            }) as missing_equipment
            RETURN f.name as facility,
                   l.name as location,
                   missing_equipment
            ORDER BY SIZE(missing_equipment) DESC
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def find_inconsistencies(self) -> List[Dict]:
        """Find capability inconsistencies"""
        query = """
            MATCH (f:Facility)-[:OFFERS_PROCEDURE]->(p:Procedure)
            MATCH (p)-[:REQUIRES_EQUIPMENT]->(e:Equipment)
            WHERE NOT (f)-[:HAS_EQUIPMENT]->(e)
            RETURN f.name as facility,
                   p.name as procedure,
                   e.name as missing_equipment
        """
        
        with self.driver.session() as session:
            result = session.run(query)
            return [dict(record) for record in result]
    
    def query_custom(self, cypher: str, params: Dict = None) -> List[Dict]:
        """Execute custom Cypher query"""
        with self.driver.session() as session:
            result = session.run(cypher, params or {})
            return [dict(record) for record in result]
    
    def get_graph_visualization(self, limit: int = 100) -> Dict:
        """Get graph data for visualization (nodes and edges)"""
        try:
            with self.driver.session() as session:
                # Get nodes
                nodes_query = f"""
                    MATCH (n)
                    RETURN id(n) as id, 
                           labels(n)[0] as label, 
                           n.name as name,
                           properties(n) as properties
                    LIMIT {limit}
                """
                nodes_result = session.run(nodes_query)
                nodes = []
                for record in nodes_result:
                    nodes.append({
                        'id': record['id'],
                        'label': record['label'],
                        'name': record['name'],
                        'properties': self._sanitize_value(dict(record['properties']))
                    })
                
                # Get ALL relationships (not limited by node selection)
                # This ensures we show all edges even if we limit nodes
                edges_query = """
                    MATCH (source)-[r]->(target)
                    RETURN id(r) as id,
                           id(source) as source,
                           id(target) as target,
                           type(r) as type,
                           properties(r) as properties
                """
                edges_result = session.run(edges_query)
                edges = []
                node_ids = {n['id'] for n in nodes}
                for record in edges_result:
                    # Only include edges where both nodes are in our node set
                    if record['source'] in node_ids and record['target'] in node_ids:
                        edges.append({
                            'id': record['id'],
                            'source': record['source'],
                            'target': record['target'],
                            'type': record['type'],
                            'properties': self._sanitize_value(dict(record['properties']))
                        })
                
                return {
                    'nodes': nodes,
                    'edges': edges
                }
        except Exception as e:
            print(f"Error getting graph visualization: {e}")
            return {'nodes': [], 'edges': []}
    
    def get_query_graph(self, query_text: str, limit: int = 50) -> Dict:
        """Get subgraph relevant to a query with matched node IDs"""
        try:
            # Extract keywords from query
            keywords = [word.lower() for word in query_text.split() 
                       if len(word) > 3 and word.lower() not in 
                       ['what', 'where', 'which', 'have', 'with', 'that', 'this', 'from']]
            
            if not keywords:
                return self.get_graph_visualization(limit)
            
            with self.driver.session() as session:
                # Search for matched nodes and return full graph with match indicators
                keyword_pattern = '|'.join(keywords[:5])  # Limit to 5 keywords
                nodes_query = f"""
                    MATCH (n)
                    WHERE toLower(n.name) =~ '(?i).*({keyword_pattern}).*'
                    WITH COLLECT(id(n)) as matchedIds
                    MATCH (n)
                    OPTIONAL MATCH (n)-[r]-(connected)
                    RETURN COLLECT(DISTINCT {{
                        id: id(n),
                        label: labels(n)[0],
                        name: n.name,
                        properties: properties(n),
                        matched: id(n) IN matchedIds
                    }}) + COLLECT(DISTINCT {{
                        id: id(connected),
                        label: labels(connected)[0],
                        name: connected.name,
                        properties: properties(connected),
                        matched: id(connected) IN matchedIds
                    }}) as nodes,
                    COLLECT(DISTINCT {{
                        id: id(r),
                        source: id(startNode(r)),
                        target: id(endNode(r)),
                        type: type(r),
                        properties: properties(r)
                    }}) as edges
                """
                
                result = session.run(nodes_query)
                record = result.single()
                
                if record:
                    nodes = [self._sanitize_value(n) for n in record['nodes'] if n.get('id') is not None]
                    edges = [self._sanitize_value(e) for e in record['edges'] if e.get('id') is not None]
                    return {'nodes': nodes, 'edges': edges}
                else:
                    return {'nodes': [], 'edges': []}
                    
        except Exception as e:
            print(f"Error getting query graph: {e}")
            return {'nodes': [], 'edges': []}
    
    def get_query_locations(self, query_text: str, limit: int = 50) -> List[Dict]:
        """
        Get Location nodes and Facility-Location pairs relevant to a query.
        Returns locations suitable for map display with facility context.
        """
        try:
            keywords = [word.lower() for word in query_text.split() 
                       if len(word) > 3 and word.lower() not in 
                       ['what', 'where', 'which', 'have', 'with', 'that', 'this', 'from']]
            
            with self.driver.session() as session:
                if keywords:
                    keyword_pattern = '|'.join(keywords[:5])
                    # Get locations: matched Locations OR Locations of matched Facilities
                    cypher = f"""
                        MATCH (n)
                        WHERE toLower(n.name) =~ '(?i).*({keyword_pattern}).*'
                        WITH COLLECT(id(n)) as matchedIds
                        MATCH (l:Location)
                        WHERE id(l) IN matchedIds
                           OR (l)<-[:LOCATED_IN]-(f:Facility) AND id(f) IN matchedIds
                        WITH DISTINCT l
                        OPTIONAL MATCH (fac:Facility)-[:LOCATED_IN]->(l)
                        WITH l, COLLECT(DISTINCT fac.name) as facilities
                        RETURN l.name as name,
                               l.city as city,
                               l.state_or_region as state_or_region,
                               l.country as country,
                               l.country_code as country_code,
                               facilities
                        LIMIT {limit}
                    """
                else:
                    # No keywords: return all Facility-Location pairs
                    cypher = """
                        MATCH (f:Facility)-[:LOCATED_IN]->(l:Location)
                        WITH l, COLLECT(DISTINCT f.name) as facilities
                        RETURN l.name as name,
                               l.city as city,
                               l.state_or_region as state_or_region,
                               l.country as country,
                               l.country_code as country_code,
                               facilities
                        LIMIT 50
                    """
                
                result = session.run(cypher)
                return [self._sanitize_value(dict(record)) for record in result]
        except Exception as e:
            print(f"Error getting query locations: {e}")
            return []
    
    def close(self):
        """Close driver"""
        self.driver.close()