// frontend/src/api/catalog.ts

const API_BASE_URL = 'http://localhost:8080/v1';

// --- Types based on openapi.yaml ---
export interface TechListResponse {
  techs: string[];
}

export type Mode = 'INLINE' | 'OFFLINE' | 'MONITOR';

export interface ProcessOption {
  process_step: string;
  intents: string[];
  modes: Mode[];
}

export interface ProcessOptionsResponse {
  process_options: ProcessOption[];
}

export interface DiePoint {
  die_x: number;
  die_y: number;
}

export interface WaferMapSpec {
  wafer_size_mm: number;
  die_pitch_x_mm: number;
  die_pitch_y_mm: number;
  origin: 'CENTER';
  notch_orientation_deg: number;
  coordinate_system: 'DIE_GRID' | 'MM' | 'SHOT';
  valid_die_mask: {
    type: 'EDGE_EXCLUSION' | 'EXPLICIT_LIST';
    radius_mm?: number;
    valid_die_list?: DiePoint[];
  };
  version: string;
}

export interface WaferMapSummary {
  wafer_map_id: string;
  tech: string;
  description: string;
}

export interface WaferMapListResponse {
  wafer_maps: WaferMapSummary[];
}

export interface ProcessContext {
  process_step: string;
  measurement_intent: string;
  mode: Mode;
  criticality: 'HIGH' | 'MEDIUM' | 'LOW';
  min_sampling_points: number;
  max_sampling_points: number;
  allowed_strategy_set: string[];
  version: string;
}

export interface ProcessContextResponse {
  process_context: ProcessContext;
}

export type CoordSystemSupported = 'DIE_GRID' | 'MM' | 'SHOT';

export interface ToolProfile {
  tool_type: string;
  vendor: string;
  model?: string;
  coordinate_system_supported: CoordSystemSupported[];
  max_points_per_wafer: number;
  edge_die_supported: boolean;
  ordering_required: boolean;
  recipe_format: {
    type: 'JSON' | 'CSV' | 'TEXT';
    version: string;
  };
  version: string;
}

export interface ToolProfileResponse {
  tool_profile: ToolProfile;
}

export interface ToolOption {
  tool_type: string;
  vendor: string;
  model?: string;
}

export interface ToolOptionsResponse {
  tool_options: ToolOption[];
}

export interface Warning {
  code: string;
  message: string;
}

export interface SamplingOutput {
  sampling_strategy_id: string;
  selected_points: DiePoint[];
  point_tags?: string[];
  trace: {
    strategy_version: string;
    generated_at: string;
  };
}

export interface SamplingPreviewRequest {
  wafer_map_spec: WaferMapSpec;
  process_context: ProcessContext;
  tool_profile: ToolProfile;
  strategy: {
    strategy_id: string;
    strategy_config?: {
      common?: {
        edge_exclusion_mm?: number;
        target_point_count?: number;
        rotation_seed?: number;
      };
      advanced?: Record<string, any>;
    };
  };
}

export interface SamplingPreviewResponse {
  sampling_output: SamplingOutput;
  warnings: Warning[];
}

export interface SamplingScoreReport {
  coverage_score: number;
  statistical_score: number;
  risk_alignment_score: number;
  overall_score: number;
  warnings: Warning[];
  version: string;
}

export interface SamplingScoreRequest {
  wafer_map_spec: WaferMapSpec;
  process_context: ProcessContext;
  tool_profile: ToolProfile;
  sampling_output: SamplingOutput;
}

export interface SamplingScoreResponse {
  score_report: SamplingScoreReport;
}

export interface ToolRecipe {
  recipe_id: string;
  tool_type: string;
  recipe_payload: Record<string, any>;
  translation_notes?: string[];
  recipe_format_version: string;
}

export interface GenerateRecipeRequest {
  wafer_map_spec: WaferMapSpec;
  tool_profile: ToolProfile;
  sampling_output: SamplingOutput;
  score_report?: SamplingScoreReport; // Optional based on openapi.yaml
}

export interface GenerateRecipeResponse {
  tool_recipe: ToolRecipe;
  warnings: Warning[];
}

// --- API Client Functions ---

// Development mock data
const MOCK_DATA = {
  techs: ['28nm', '22nm', '16nm', '14nm', '10nm', '7nm', '5nm', '3nm'],
  waferMaps: [
    { wafer_map_id: 'standard_300mm', tech: '28nm', description: 'Standard 300mm wafer layout' },
    { wafer_map_id: 'high_density_300mm', tech: '28nm', description: 'High density 300mm layout' },
    { wafer_map_id: 'test_200mm', tech: '28nm', description: 'Test 200mm wafer layout' },
  ],
  processOptions: [
    { process_step: 'lithography', intents: ['critical_dimension', 'overlay'], modes: ['INLINE', 'OFFLINE'] as Mode[] },
    { process_step: 'etch', intents: ['depth', 'uniformity'], modes: ['INLINE', 'MONITOR'] as Mode[] },
    { process_step: 'metal', intents: ['resistance', 'thickness'], modes: ['OFFLINE', 'MONITOR'] as Mode[] },
  ],
  toolOptions: [
    { tool_type: 'SEM', vendor: 'ASML', model: 'eSEM-1000' },
    { tool_type: 'AFM', vendor: 'Bruker', model: 'Dimension-FastScan' },
    { tool_type: 'Optical', vendor: 'KLA', model: 'Archer-750' },
  ]
};

async function fetchAPI<T>(url: string, options?: RequestInit): Promise<T> {
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({ message: 'Unknown error' }));
      throw new Error(
        `HTTP error! status: ${response.status} - ${errorBody.error?.message || 'No error message'}`,
      );
    }
    return response.json();
  } catch (error) {
    console.warn(`API call failed: ${url}. Using mock data for development.`);
    throw error; // Let individual functions handle with mock data
  }
}

export const listTechs = async (): Promise<TechListResponse> => {
  try {
    return await fetchAPI<TechListResponse>(`${API_BASE_URL}/catalog/techs`);
  } catch {
    console.log('Using mock techs data');
    return Promise.resolve({ techs: MOCK_DATA.techs });
  }
};

export const listProcessOptions = async (tech: string): Promise<ProcessOptionsResponse> => {
  try {
    return await fetchAPI<ProcessOptionsResponse>(`${API_BASE_URL}/catalog/process-options?tech=${tech}`);
  } catch {
    console.log('Using mock process options data');
    return Promise.resolve({ process_options: MOCK_DATA.processOptions });
  }
};

export const listWaferMaps = async (tech: string): Promise<WaferMapListResponse> => {
  try {
    return await fetchAPI<WaferMapListResponse>(`${API_BASE_URL}/catalog/wafer-maps?tech=${tech}`);
  } catch {
    console.log('Using mock wafer maps data');
    return Promise.resolve({ wafer_maps: MOCK_DATA.waferMaps });
  }
};

// v1 Proposal: This endpoint is missing. We need a way to get the full WaferMapSpec from a wafer_map_id.
// For now, returning a mock spec.
export const getWaferMapSpec = async (waferMapId: string): Promise<WaferMapSpec> => {
  console.warn(`[MOCK] getWaferMapSpec called for ${waferMapId}. Returning mock data.`);
  return Promise.resolve({
    wafer_size_mm: 300,
    die_pitch_x_mm: 10,
    die_pitch_y_mm: 10,
    origin: 'CENTER',
    notch_orientation_deg: 270,
    coordinate_system: 'DIE_GRID',
    valid_die_mask: { type: 'EDGE_EXCLUSION', radius_mm: 145 },
    version: 'mock-v1',
  });
};

export const getProcessContext = async (params: { tech: string; step: string; intent: string; mode: Mode }): Promise<ProcessContextResponse> => {
  try {
    return await fetchAPI<ProcessContextResponse>(
      `${API_BASE_URL}/catalog/process-context?tech=${params.tech}&step=${params.step}&intent=${params.intent}&mode=${params.mode}`,
    );
  } catch {
    console.log('Using mock process context data');
    return Promise.resolve({
      process_context: {
        process_step: params.step,
        measurement_intent: params.intent,
        mode: params.mode,
        criticality: 'MEDIUM' as const,
        min_sampling_points: 10,
        max_sampling_points: 100,
        allowed_strategy_set: ['CENTER_EDGE', 'RANDOM_UNIFORM', 'GRID'],
        version: 'mock-v1'
      }
    });
  }
};

export const listToolOptions = async (params: { tech: string; step: string; intent: string }): Promise<ToolOptionsResponse> => {
  try {
    return await fetchAPI<ToolOptionsResponse>(
      `${API_BASE_URL}/catalog/tool-options?tech=${params.tech}&step=${params.step}&intent=${params.intent}`,
    );
  } catch {
    console.log('Using mock tool options data');
    return Promise.resolve({ tool_options: MOCK_DATA.toolOptions });
  }
};

export const getToolProfile = async (toolType: string): Promise<ToolProfileResponse> => {
  try {
    return await fetchAPI<ToolProfileResponse>(`${API_BASE_URL}/catalog/tool-profile?toolType=${toolType}`);
  } catch {
    console.log('Using mock tool profile data');
    return Promise.resolve({
      tool_profile: {
        tool_type: toolType,
        vendor: 'MockVendor',
        model: 'MockModel-1000',
        coordinate_system_supported: ['DIE_GRID', 'MM'] as CoordSystemSupported[],
        max_points_per_wafer: 1000,
        edge_die_supported: true,
        ordering_required: false,
        recipe_format: {
          type: 'JSON' as const,
          version: '1.0'
        },
        version: 'mock-v1'
      }
    });
  }
};

export const previewSampling = (requestBody: SamplingPreviewRequest) =>
  fetchAPI<SamplingPreviewResponse>(`${API_BASE_URL}/sampling/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody),
  });

export const scoreSampling = (requestBody: SamplingScoreRequest) =>
  fetchAPI<SamplingScoreResponse>(`${API_BASE_URL}/sampling/score`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody),
  });

export const generateRecipe = (requestBody: GenerateRecipeRequest) =>
  fetchAPI<GenerateRecipeResponse>(`${API_BASE_URL}/recipes/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestBody),
  });
