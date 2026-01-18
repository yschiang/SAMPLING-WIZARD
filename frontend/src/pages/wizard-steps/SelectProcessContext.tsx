import { useContext, useEffect, useState } from 'react';
import { Check, Settings, Activity } from 'lucide-react';
import { WizardContext } from '../../context/WizardContext';
import { listProcessOptions, getProcessContext } from '../../api/catalog';
import type { ProcessOption, Mode } from '../../api/catalog';
import { Badge } from '../../ui/Badge';

const SelectProcessContext = () => {
  const { state, dispatch } = useContext(WizardContext);
  const [availableProcessOptions, setAvailableProcessOptions] = useState<ProcessOption[]>([]);

  const { tech: selectedTech } = state.inputs;

  useEffect(() => {
    if (selectedTech) {
      const fetchProcessOptions = async () => {
        dispatch({ type: 'SET_LOADING', payload: true });
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

  if (!selectedTech) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-in">
        <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-4">
          <Settings className="h-6 w-6 text-muted-foreground" />
        </div>
        <h2 className="text-xl font-medium">Context Required</h2>
        <p className="text-muted-foreground max-w-xs">Complete technology selection to define process context.</p>
      </div>
    );
  }

  return (
    <div className="space-y-10 animate-fade-in max-w-4xl mx-auto">
      {/* Header Section */}
      <div className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">Process Context</h2>
        <p className="text-muted-foreground">
          Define the measurement intent and operational mode for this sampling cycle.
        </p>
      </div>

      <div className="grid gap-8">
        {availableProcessOptions.map((pOption) => {
          const isActiveStep = state.inputs.processContext.processStep === pOption.process_step;
          
          return (
            <section key={pOption.process_step} className="space-y-4">
              <div className="flex items-center gap-3 px-1">
                <div className="h-8 w-8 rounded bg-muted flex items-center justify-center">
                  <Activity className="h-4 w-4 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-semibold uppercase tracking-wider text-muted-foreground/80">
                  Step: {pOption.process_step}
                </h3>
                {isActiveStep && (
                  <Badge variant="outline" className="ml-auto bg-success/5 text-success border-success/20">
                    <Check className="h-3 w-3 mr-1" /> Configured
                  </Badge>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {pOption.intents.flatMap((intent) =>
                  pOption.modes.map((mode) => {
                    const isSelected = 
                      state.inputs.processContext.processStep === pOption.process_step &&
                      state.inputs.processContext.measurementIntent === intent &&
                      state.inputs.processContext.mode === mode;
                    
                    return (
                      <button
                        key={`${intent}-${mode}`}
                        onClick={() => handleSelectProcessContext(pOption, intent, mode)}
                        className={`
                          group relative flex flex-col p-5 rounded-xl border text-left transition-all
                          ${isSelected ? 'border-primary ring-1 ring-primary bg-primary/[0.02]' : 'hover:bg-muted/50 border-border bg-card'}
                        `}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className={`font-semibold ${isSelected ? 'text-primary' : 'text-foreground'}`}>
                            {intent.replace('_', ' ')}
                          </span>
                          <Badge variant="secondary" className="text-[10px] uppercase font-bold tracking-widest">
                            {mode}
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          Measurement optimization for {intent.toLowerCase()} in {mode.toLowerCase()} environment.
                        </p>
                        {isSelected && (
                          <div className="absolute top-2 right-2">
                            <div className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
                          </div>
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
};

export default SelectProcessContext;