export interface Assertion {
  type: string;
  value?: string;
  rubric?: string;
}

export interface TestCase {
  id?: string;
  eval_set_id?: string;
  prompt_input: string;
  expected_output: string;
  context?: string | null;
  rubric: string;
  difficulty: "easy" | "medium" | "hard" | "adversarial";
  tags: string[];
  assertions?: Assertion[];
  created_at?: string;
}

export interface EvalSet {
  id: string;
  title: string;
  description?: string;
  domain: string;
  eval_type: string;
  target_capability?: string;
  created_at: string;
  updated_at: string;
  total_test_cases?: number;
  test_cases: TestCase[];
}

export interface GenerationRequest {
  title: string;
  prompt_scenario: string;
  domain: string;
  eval_type: string;
  num_samples: number;
  include_adversarial: boolean;
  context_documents?: string[];
  auto_save: boolean;
}

export interface GenerationResponse {
  success: boolean;
  eval_set_id?: string;
  message: string;
  dataset: {
    title: string;
    description: string;
    domain: string;
    eval_type: string;
    target_capability: string;
    test_cases: TestCase[];
  };
  model_used?: string;
  retry_count: number;
}

export interface AppConfig {
  app_name: string;
  environment: string;
  gemini_model: string;
  gemini_configured: boolean;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details?: Record<string, any>;
  retryable: boolean;
  retry_count: number;
  trace_id: string;
  timestamp: string;
}

export interface BenchmarkRunRequest {
  system_prompt?: string;
  model_name?: string;
}

export interface EvaluationResult {
  id: string;
  test_case_id: string;
  prompt_input?: string;
  expected_output?: string;
  context?: string | null;
  rubric?: string | null;
  difficulty?: string;
  actual_output?: string;
  passed: boolean;
  score: number;
  feedback?: string;
  latency_ms?: number;
  created_at: string;
}

export interface EvalRun {
  id: string;
  eval_set_id: string;
  model_tested: string;
  system_prompt?: string;
  status: string;
  overall_score?: number;
  passed_count: number;
  total_count: number;
  accuracy_rate: number;
  created_at: string;
  results: EvaluationResult[];
}

export interface ErrorEnvelope {
  success: false;
  error: ErrorDetail;
}
