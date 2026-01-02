import { useContext, useEffect, useState } from 'react';
import { WizardContext } from '../../context/WizardContext';
import { listToolOptions, getToolProfile } from '../../api/catalog';
import type { ToolOption } from '../../api/catalog';

const SelectToolType = () => {
  const { state, dispatch } = useContext(WizardContext);
  const [availableToolOptions, setAvailableToolOptions] = useState<ToolOption[]>([]);

  const { tech, processContext: processContextInputs } = state.inputs;

  useEffect(() => {
    if (tech && processContextInputs.processStep && processContextInputs.measurementIntent) {
      const fetchToolOptions = async () => {
        dispatch({ type: 'SET_LOADING', payload: true });
        dispatch({ type: 'SET_ERROR', payload: null });
        try {
          const response = await listToolOptions({
            tech: tech!,
            step: processContextInputs.processStep!,
            intent: processContextInputs.measurementIntent!,
          });
          setAvailableToolOptions(response.tool_options);
        } catch (err: any) {
          dispatch({ type: 'SET_ERROR', payload: err.message });
        } finally {
          dispatch({ type: 'SET_LOADING', payload: false });
        }
      };
      fetchToolOptions();
    } else {
      setAvailableToolOptions([]);
    }
  }, [tech, processContextInputs, dispatch]);

  const handleSelectTool = async (tool: ToolOption) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });
    try {
      const response = await getToolProfile(tool.tool_type);
      dispatch({
        type: 'SET_TOOL_PROFILE',
        payload: {
          inputs: { toolType: tool.tool_type, vendor: tool.vendor, model: tool.model },
          derived: response.tool_profile,
        },
      });
    } catch (err: any) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  return (
    <div>
      <h3>Step 3: Select Tool Type</h3>
      {state.isLoading && <p>Loading...</p>}
      {state.error && <p style={{ color: 'red' }}>Error: {state.error}</p>}
      {!tech && !processContextInputs.processStep && (
        <p>Please complete previous steps first.</p>
      )}
      <p>Current Tool Selection: {JSON.stringify(state.inputs.tool)}</p>
      <p style={{ fontSize: '0.8em', color: 'gray' }}>
        Full Derived Profile: {JSON.stringify(state.derived.toolProfile, null, 2)}
      </p>
      {availableToolOptions.map((tool) => (
        <button
          key={tool.tool_type}
          onClick={() => handleSelectTool(tool)}
          disabled={state.isLoading}
          style={{
            fontWeight: state.inputs.tool.toolType === tool.tool_type ? 'bold' : 'normal',
          }}
        >
          {tool.tool_type} {tool.vendor && `(${tool.vendor})`}
        </button>
      ))}
    </div>
  );
};

export default SelectToolType;
