export interface SkillMetadata {
  emoji?: string | null;
  skill_key?: string | null;
  primary_env?: string | null;
  requires?: {
    env?: string[];
    config?: string[];
    bins?: string[];
  };
}

export interface SkillEligibilityStatus {
  eligible: boolean;
  disabled: boolean;
  missing_env: string[];
  missing_config: string[];
  missing_bins: string[];
}

export interface SkillConfigStatus {
  key: string;
  enabled?: boolean | null;
  has_api_key: boolean;
  env_keys: string[];
  config_keys: string[];
}

export interface SkillSpec {
  name: string;
  description?: string;
  content: string;
  source: string;
  path: string;
  enabled?: boolean;
  metadata?: SkillMetadata | null;
  resolved_skill_key?: string;
  eligibility?: SkillEligibilityStatus | null;
  config_status?: SkillConfigStatus | null;
}

export interface SkillConfigView {
  key: string;
  enabled?: boolean | null;
  has_api_key: boolean;
  env: Record<string, string>;
  config: Record<string, unknown>;
  env_keys: string[];
  config_keys: string[];
}

export interface SkillConfigUpdatePayload {
  enabled?: boolean | null;
  apiKey?: string;
  clearApiKey?: boolean;
  env?: Record<string, string>;
  config?: Record<string, unknown>;
}

export interface HubSkillSpec {
  slug: string;
  name: string;
  description: string;
  version: string;
  source_url: string;
}

// Legacy Skill interface for backward compatibility
export interface Skill {
  id: string;
  name: string;
  description: string;
  function_name: string;
  enabled: boolean;
  version: string;
  tags: string[];
  created_at: number;
  updated_at: number;
}
