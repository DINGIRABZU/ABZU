// Neo4j schema and migration script for agent events
// Node constraints and indexes
CREATE CONSTRAINT agent_id_unique IF NOT EXISTS
FOR (a:Agent) REQUIRE a.agent_id IS UNIQUE;

CREATE INDEX event_time_idx IF NOT EXISTS
FOR (e:Event) ON (e.timestamp);

CREATE INDEX event_type_idx IF NOT EXISTS
FOR (e:Event) ON (e.event_type);

// Relationship queries
// Retrieve recent events for an agent
// MATCH (a:Agent {agent_id: $agent_id})-[:EMITTED]->(e:Event)
// RETURN e ORDER BY e.timestamp DESC LIMIT 100;

// Find co-emission counts between agents
// MATCH (a1:Agent)-[:EMITTED]->(e:Event)<-[:EMITTED]-(a2:Agent)
// RETURN a1.agent_id AS source, a2.agent_id AS collaborator, COUNT(e) AS interactions
// ORDER BY interactions DESC;
