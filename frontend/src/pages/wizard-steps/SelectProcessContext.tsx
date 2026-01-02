import { useContext, useEffect, useState } from 'react';
import { WizardContext } from '../../context/WizardContext';
import { listProcessOptions, getProcessContext } from '../../api/catalog';
import type { ProcessOption, Mode } from '../../api/catalog';

const SelectProcessContext = () => {
  const { state, dispatch } = useContext(WizardContext);
  const [availableProcessOptions, setAvailableProcessOptions] = useState<ProcessOption[]>([]);

  const { tech: selectedTech } = state.inputs;

  useEffect(() => {
    if (selectedTech) {
      const fetchProcessOptions = async () => {
        dispatch({ type: 'SET_LOADING', payload: true });
        dispatch({ type: 'SET_ERROR', payload: null });
        try {
          const response = await listProcessOptions(selectedTech);
          setAvailableProcessOptions(response.process_options);
        } catch (err: any) {
          dispatch({ type: 'SET_ERROR', payload: err.message });
        } finally {
          dispatch({ type: 'SET_LOADING', payload: false });
        }
      };
      fetchProcessOptions();
    } else {
      setAvailableProcessOptions([]);
    }
  }, [selectedTech, dispatch]);

  const handleSelectProcessContext = async (pOption: ProcessOption, intent: string, mode: Mode) => {
    if (!selectedTech) return;
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });
    try {
      const response = await getProcessContext({
        tech: selectedTech,
        step: pOption.process_step,
        intent: intent,
        mode: mode,
      });
      dispatch({
        type: 'SET_PROCESS_CONTEXT',
        payload: {
          inputs: {
            processStep: pOption.process_step,
            measurementIntent: intent,
            mode: mode,
          },
          derived: response.process_context,
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
      <h3>Step 2: Select Process Context</h3>
      {state.isLoading && <p>Loading...</p>}
      {state.error && <p style={{ color: 'red' }}>Error: {state.error}</p>}
      {!selectedTech && <p>Please select a Tech in Step 1 first.</p>}

      <p>
        Current Process Context Inputs: {JSON.stringify(state.inputs.processContext)}
      </p>
      <p style={{ fontSize: '0.8em', color: 'gray' }}>
        Full Derived Context: {JSON.stringify(state.derived.processContext, null, 2)}
      </p>

      {selectedTech && availableProcessOptions.length > 0 && (
        <div>
          {availableProcessOptions.map((pOption) => (
            <div key={pOption.process_step} style={{ border: '1px solid gray', margin: '10px', padding: '10px' }}>
              <h4>Process Step: {pOption.process_step}</h4>
              {pOption.intents.map((intent) => (
                <div key={intent}>
                  {pOption.modes.map((mode) => (
                    <button
                      key={`${intent}-${mode}`}
                      onClick={() => handleSelectProcessContext(pOption, intent, mode)}
                      disabled={state.isLoading}
                      style={{
                        fontWeight:
                          state.inputs.processContext.processStep === pOption.process_step &&
                          state.inputs.processContext.measurementIntent === intent &&
                          state.inputs.processContext.mode === mode
                            ? 'bold'
                            : 'normal',
                      }}
                    >
                      {intent} ({mode})
                    </button>
                  ))}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SelectProcessContext;
