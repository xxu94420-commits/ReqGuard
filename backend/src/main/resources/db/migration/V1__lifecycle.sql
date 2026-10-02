CREATE TABLE requirements (
 id VARCHAR(36) PRIMARY KEY, title VARCHAR(200) NOT NULL, original_text TEXT NOT NULL,
 type VARCHAR(40) NOT NULL, priority VARCHAR(20) NOT NULL, source VARCHAR(40) NOT NULL,
 owner VARCHAR(120) NOT NULL, project VARCHAR(120) NOT NULL, issue_url VARCHAR(500),
 issue_id INTEGER, created_at VARCHAR(40) NOT NULL
);
CREATE TABLE versions (
 id VARCHAR(36) PRIMARY KEY, requirement_id VARCHAR(36) NOT NULL REFERENCES requirements(id),
 number INTEGER NOT NULL, text TEXT NOT NULL, reason VARCHAR(500) NOT NULL, created_at VARCHAR(40) NOT NULL,
 UNIQUE(requirement_id, number)
);
CREATE TABLE records (
 id VARCHAR(36) PRIMARY KEY, requirement_id VARCHAR(36) NOT NULL REFERENCES requirements(id),
 version_id VARCHAR(36) NOT NULL REFERENCES versions(id), kind VARCHAR(30) NOT NULL,
 payload TEXT NOT NULL, created_at VARCHAR(40) NOT NULL
);
CREATE INDEX records_requirement_kind ON records(requirement_id, kind);
