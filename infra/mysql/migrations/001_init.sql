CREATE TABLE IF NOT EXISTS projects (
  id VARCHAR(50) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  goal TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS artifacts (
  id VARCHAR(50) PRIMARY KEY,
  project_id VARCHAR(50) NOT NULL,
  type VARCHAR(50) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_artifacts_projects FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS sections (
  id VARCHAR(50) PRIMARY KEY,
  artifact_id VARCHAR(50) NOT NULL,
  section_name VARCHAR(100) NOT NULL,
  content JSON NOT NULL,
  version INT NOT NULL DEFAULT 1,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CONSTRAINT fk_sections_artifacts FOREIGN KEY (artifact_id) REFERENCES artifacts(id),
  UNIQUE KEY uq_sections_artifact_section (artifact_id, section_name)
);

CREATE TABLE IF NOT EXISTS section_versions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  section_id VARCHAR(50) NOT NULL,
  version INT NOT NULL,
  content JSON NOT NULL,
  change_reason VARCHAR(100) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_section_versions_sections FOREIGN KEY (section_id) REFERENCES sections(id)
);

CREATE TABLE IF NOT EXISTS refinement_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  section_id VARCHAR(50) NULL,
  user_input TEXT NULL,
  action_type VARCHAR(50) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_refinement_logs_sections FOREIGN KEY (section_id) REFERENCES sections(id)
);

CREATE TABLE IF NOT EXISTS checkpoints (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  project_id VARCHAR(50) NOT NULL,
  graph_state JSON NOT NULL,
  current_node VARCHAR(100) NOT NULL,
  status VARCHAR(50) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_checkpoints_projects FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS llm_logs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  project_id VARCHAR(50) NOT NULL,
  artifact_id VARCHAR(50) NULL,
  section_id VARCHAR(50) NULL,
  node_name VARCHAR(100) NOT NULL,
  agent_name VARCHAR(100) NOT NULL,
  model_name VARCHAR(100) NOT NULL,
  prompt_template_version VARCHAR(50) NULL,
  system_prompt TEXT NOT NULL,
  user_prompt TEXT NOT NULL,
  context_payload JSON NOT NULL,
  response_text LONGTEXT NULL,
  response_format VARCHAR(50) NOT NULL DEFAULT 'json',
  status VARCHAR(50) NOT NULL,
  error_message TEXT NULL,
  input_tokens INT NOT NULL DEFAULT 0,
  output_tokens INT NOT NULL DEFAULT 0,
  total_tokens INT NOT NULL DEFAULT 0,
  estimated_cost DECIMAL(10, 6) NOT NULL DEFAULT 0,
  latency_ms INT NOT NULL DEFAULT 0,
  cache_hit BOOLEAN NOT NULL DEFAULT FALSE,
  cache_key VARCHAR(128) NULL,
  start_time TIMESTAMP NULL,
  end_time TIMESTAMP NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_llm_logs_projects FOREIGN KEY (project_id) REFERENCES projects(id),
  CONSTRAINT fk_llm_logs_artifacts FOREIGN KEY (artifact_id) REFERENCES artifacts(id),
  CONSTRAINT fk_llm_logs_sections FOREIGN KEY (section_id) REFERENCES sections(id)
);

CREATE TABLE IF NOT EXISTS llm_context_chunks (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  llm_log_id BIGINT NOT NULL,
  chunk_id VARCHAR(100) NOT NULL,
  relevance_score DECIMAL(8, 6) NOT NULL DEFAULT 0,
  source_type VARCHAR(50) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_llm_context_chunks_logs FOREIGN KEY (llm_log_id) REFERENCES llm_logs(id)
);

CREATE TABLE IF NOT EXISTS rag_sources (
  id VARCHAR(50) PRIMARY KEY,
  project_id VARCHAR(50) NOT NULL,
  file_name VARCHAR(255) NOT NULL,
  source_type VARCHAR(50) NOT NULL,
  content_hash VARCHAR(64) NOT NULL,
  chunk_count INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_rag_sources_projects FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS llm_response_cache (
  cache_key VARCHAR(128) PRIMARY KEY,
  model_name VARCHAR(100) NOT NULL,
  response_text LONGTEXT NOT NULL,
  input_tokens INT NOT NULL DEFAULT 0,
  output_tokens INT NOT NULL DEFAULT 0,
  context_payload JSON NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS project_llm_settings (
  project_id VARCHAR(50) NOT NULL,
  agent_name VARCHAR(50) NOT NULL,
  provider VARCHAR(50) NOT NULL,
  model VARCHAR(100) NOT NULL,
  token_budget INT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (project_id, agent_name),
  CONSTRAINT fk_project_llm_settings_projects FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX idx_artifacts_project_id ON artifacts(project_id);
CREATE INDEX idx_sections_artifact_id ON sections(artifact_id);
CREATE INDEX idx_section_versions_section_id ON section_versions(section_id);
CREATE INDEX idx_checkpoints_project_id ON checkpoints(project_id);
CREATE INDEX idx_llm_logs_project_id ON llm_logs(project_id);
CREATE INDEX idx_llm_logs_section_id ON llm_logs(section_id);
CREATE INDEX idx_llm_logs_node_name ON llm_logs(node_name);
CREATE INDEX idx_llm_logs_created_at ON llm_logs(created_at);
CREATE INDEX idx_rag_sources_project_id ON rag_sources(project_id);
