import { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { WizardContext } from '../../context/WizardContext';
import { previewSampling, scoreSampling } from '../../api/catalog';

const SelectSamplingStrategy = () => {
  const { state, dispatch } = useContext(WizardContext);
  const navigate = useNavigate();

  const handleSelectStrategy = (strategyId: string) => {
    dispatch({ type: 'SET_STRATEGY', payload: strategyId });
  };

  const handlePreviewAndScore = async () => {
    const { waferMapSpec, processContext, toolProfile } = state.derived;
    const { strategyId } = state.inputs.strategy;

    if (!waferMapSpec || !processContext || !toolProfile || !strategyId) {
      dispatch({
        type: 'SET_ERROR',
        payload: 'Cannot run preview. Missing one or more required inputs from previous steps.',
      });
      return;
    }

    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      // Step 1: Preview
      const previewResponse = await previewSampling({
        wafer_map_spec: waferMapSpec,
        process_context: processContext,
        tool_profile: toolProfile,
        strategy: { strategy_id: strategyId },
      });
      dispatch({ type: 'SET_PREVIEW_OUTPUT', payload: { 
        samplingOutput: previewResponse.sampling_output, 
        warnings: previewResponse.warnings 
      } });

      // Step 2: Score (using the output from preview)
      const scoreResponse = await scoreSampling({
        wafer_map_spec: waferMapSpec,
        process_context: processContext,
        tool_profile: toolProfile,
        sampling_output: previewResponse.sampling_output,
      });
      dispatch({ type: 'SET_SCORE_REPORT', payload: scoreResponse.score_report });

      navigate('/wizard/preview-sampling-and-scoring');
    } catch (err: any) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const allowedStrategies = state.derived.processContext?.allowed_strategy_set || [];

  return (
    <div>
      <h3>Step 4: Select Sampling Strategy</h3>
      {state.isLoading && <p>Loading...</p>}
      {state.error && <p style={{ color: 'red' }}>Error: {state.error}</p>}
      {!state.derived.processContext && <p>Please complete previous steps first.</p>}

      <p>Current Strategy: {state.inputs.strategy.strategyId || 'None'}</p>

      {allowedStrategies.map((strategy) => (
        <button
          key={strategy}
          onClick={() => handleSelectStrategy(strategy)}
          style={{
            fontWeight: state.inputs.strategy.strategyId === strategy ? 'bold' : 'normal',
          }}
        >
          {strategy}
        </button>
      ))}

      <div style={{ marginTop: '20px' }}>
        <button onClick={handlePreviewAndScore} disabled={state.isLoading || !state.inputs.strategy.strategyId}>
          Preview & Score Sampling
        </button>
      </div>
    </div>
  );
};

export default SelectSamplingStrategy;
