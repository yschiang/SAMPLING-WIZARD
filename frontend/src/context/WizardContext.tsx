import { createContext, useReducer } from 'react';
import type { ReactNode, Dispatch } from 'react';
import type {
  WaferMapSpec,
  ProcessContext,
  ToolProfile,
  SamplingOutput,
  Warning,
  SamplingScoreReport,
  ToolRecipe,
} from '../api/catalog';

// 1. Define State Shape
export interface WizardState {
  currentStep: number;
  inputs: {
    tech: string | null;
    waferMapId: string | null;
    processContext: {
      processStep: string | null;
      measurementIntent: string | null;
      mode: string | null;
    };
    tool: {
      toolType: string | null;
      vendor?: string | null;
      model?: string | null;
    };
    strategy: {
      strategyId: string | null;
      strategy_config?: {
        common?: {
          edge_exclusion_mm?: number;
          target_point_count?: number;
          rotation_seed?: number;
        };
        specific?: Record<string, any>;
      };
    };
  };
  derived: {
    waferMapSpec: WaferMapSpec | null;
    processContext: ProcessContext | null;
    toolProfile: ToolProfile | null;
  };
  outputs: {
    samplingOutput: SamplingOutput | null;
    previewWarnings: Warning[];
    scoreReport: SamplingScoreReport | null;
    toolRecipe: ToolRecipe | null;
  };
  isLoading: boolean;
  error: string | null;
}

// 2. Define Initial State
export const initialState: WizardState = {
  currentStep: 1,
  inputs: {
    tech: null,
    waferMapId: null,
    processContext: {
      processStep: null,
      measurementIntent: null,
      mode: null,
    },
    tool: {
      toolType: null,
    },
    strategy: {
      strategyId: null,
      strategy_config: {
        common: {
          edge_exclusion_mm: 5,
          target_point_count: 100,
          rotation_seed: 0
        }
      }
    },
  },
  derived: {
    waferMapSpec: null,
    processContext: null,
    toolProfile: null,
  },
  outputs: {
    samplingOutput: null,
    previewWarnings: [],
    scoreReport: null,
    toolRecipe: null,
  },
  isLoading: false,
  error: null,
};

// 3. Define Action Types
type Action =
  | { type: 'GO_TO_NEXT_STEP' }
  | { type: 'GO_TO_PREVIOUS_STEP' }
  | { type: 'SET_TECH'; payload: string }
  | { type: 'SET_WAFER_MAP'; payload: { id: string; spec: WaferMapSpec } }
  | { type: 'SET_PROCESS_CONTEXT'; payload: { inputs: WizardState['inputs']['processContext']; derived: ProcessContext } }
  | { type: 'SET_TOOL_PROFILE'; payload: { inputs: WizardState['inputs']['tool']; derived: ToolProfile } }
  | { type: 'SET_STRATEGY'; payload: string }
  | { type: 'SET_STRATEGY_PARAMS'; payload: Record<string, any> }
  | { type: 'SET_PREVIEW_OUTPUT'; payload: { samplingOutput: SamplingOutput; warnings: Warning[] } }
  | { type: 'SET_SCORE_REPORT'; payload: SamplingScoreReport }
  | { type: 'SET_RECIPE_OUTPUT'; payload: ToolRecipe }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null };

// 4. Create the Reducer
const wizardReducer = (state: WizardState, action: Action): WizardState => {
  switch (action.type) {
    case 'GO_TO_NEXT_STEP':
      return { ...state, currentStep: state.currentStep + 1 };
    case 'GO_TO_PREVIOUS_STEP':
      return { ...state, currentStep: state.currentStep - 1 };
    case 'SET_TECH':
      return {
        ...initialState,
        currentStep: state.currentStep,
        inputs: {
          ...initialState.inputs,
          tech: action.payload,
        },
      };
    case 'SET_WAFER_MAP':
      return {
        ...state,
        inputs: { ...state.inputs, waferMapId: action.payload.id },
        derived: { ...state.derived, waferMapSpec: action.payload.spec },
      };
    case 'SET_PROCESS_CONTEXT':
      return {
        ...state,
        inputs: {
          ...state.inputs,
          processContext: action.payload.inputs,
        },
        derived: {
          ...state.derived,
          processContext: action.payload.derived,
        },
      };
    case 'SET_TOOL_PROFILE':
      return {
        ...state,
        inputs: {
          ...state.inputs,
          tool: action.payload.inputs,
        },
        derived: {
          ...state.derived,
          toolProfile: action.payload.derived,
        },
      };
    case 'SET_STRATEGY':
      return { 
        ...state, 
        inputs: { 
          ...state.inputs, 
          strategy: { 
            strategyId: action.payload,
            strategy_config: {
              common: {
                edge_exclusion_mm: 5,
                target_point_count: 100,
                rotation_seed: 0
              }
            }
          } 
        } 
      };
    case 'SET_STRATEGY_PARAMS':
      return {
        ...state,
        inputs: {
          ...state.inputs,
          strategy: {
            ...state.inputs.strategy,
            strategy_config: {
              ...state.inputs.strategy.strategy_config,
              common: { 
                ...state.inputs.strategy.strategy_config?.common, 
                ...action.payload 
              }
            }
          }
        }
      };
    case 'SET_PREVIEW_OUTPUT':
      return {
        ...state,
        outputs: {
          ...state.outputs,
          samplingOutput: action.payload.samplingOutput,
          previewWarnings: action.payload.warnings,
          scoreReport: null,
          toolRecipe: null,
        },
      };
    case 'SET_SCORE_REPORT':
      return {
        ...state,
        outputs: {
          ...state.outputs,
          scoreReport: action.payload,
          toolRecipe: null,
        },
      };
    case 'SET_RECIPE_OUTPUT':
      return {
        ...state,
        outputs: {
          ...state.outputs,
          toolRecipe: action.payload,
        },
      };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };
    default:
      return state;
  }
};

// 5. Create the Context
export const WizardContext = createContext<{
  state: WizardState;
  dispatch: Dispatch<Action>;
}>({
  state: initialState,
  dispatch: () => null,
});

// 6. Create the Provider Component
export const WizardProvider = ({ children }: { children: ReactNode }) => {
  const [state, dispatch] = useReducer(wizardReducer, initialState);

  return (
    <WizardContext.Provider value={{ state, dispatch }}>
      {children}
    </WizardContext.Provider>
  );
};