import { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Check, Play, BarChart2, Info } from 'lucide-react';
import { WizardContext } from '../../context/WizardContext';
import { previewSampling, scoreSampling } from '../../api/catalog';
import { Button } from '../../ui/Button';
import { StrategyPreview } from '../../components/StrategyPreview';

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
        payload: 'Cannot run preview. Missing required configuration context.',
      });
      return;
    }

    dispatch({ type: 'SET_LOADING', payload: true });

    try {
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

  if (!state.derived.processContext) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-in">
        <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-4">
          <Info className="h-6 w-6 text-muted-foreground" />
        </div>
        <h2 className="text-xl font-medium">Strategy Locked</h2>
        <p className="text-muted-foreground max-w-xs">Define process and tool context to unlock sampling strategies.</p>
      </div>
    );
  }

  return (
    <div className="space-y-10 animate-fade-in max-w-6xl mx-auto">
      {/* Header Section */}
      <div className="space-y-2 text-center md:text-left">
        <h2 className="text-2xl font-semibold tracking-tight">Sampling Strategy</h2>
        <p className="text-muted-foreground">
          Choose a mathematical distribution model optimized for defect detection.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {allowedStrategies.map((strategy) => {
          const isSelected = state.inputs.strategy.strategyId === strategy;
          return (
            <button
              key={strategy}
              onClick={() => handleSelectStrategy(strategy)}
              className={`
                group relative flex flex-col items-center text-center p-6 rounded-xl border-2 transition-all duration-200 h-full
                ${isSelected 
                  ? 'border-primary ring-1 ring-primary/50 bg-primary/[0.02] shadow-md' 
                  : 'border-border/60 hover:border-primary/30 hover:bg-muted/30 bg-card'
                }
              `}
            >
              {/* Selection Radio Indicator */}
              <div className="absolute top-4 right-4">
                <div className={`
                  h-5 w-5 rounded-full border-2 flex items-center justify-center transition-colors
                  ${isSelected ? 'border-primary bg-primary' : 'border-muted-foreground/30'}
                `}>
                  {isSelected && <Check className="h-3 w-3 text-primary-foreground" />}
                </div>
              </div>

              {/* Preview Visualization */}
              <div className="mb-6 mt-2 opacity-90 group-hover:opacity-100 transition-opacity">
                <StrategyPreview strategyId={strategy} />
              </div>

              {/* Content */}
              <div className="space-y-3 flex-1 flex flex-col justify-end w-full">
                <div className="space-y-1">
                  <h3 className={`font-semibold text-sm ${isSelected ? 'text-primary' : 'text-foreground'}`}>
                    {strategy.replace(/_/g, ' ')}
                  </h3>
                  <p className="text-xs text-muted-foreground leading-relaxed line-clamp-3">
                    System algorithm for process-specific coordinate generation.
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* CTA Section */}
      <div className="flex flex-col items-center pt-12 space-y-4 border-t border-border/40">
        <Button
          size="lg"
          onClick={handlePreviewAndScore}
          disabled={state.isLoading || !state.inputs.strategy.strategyId}
          className="w-full max-w-sm h-14 text-base font-semibold shadow-xl transition-all active:scale-[0.98] bg-primary hover:bg-primary/90"
        >
          {state.isLoading ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Running Analysis...
            </>
          ) : (
            <>
              <Play className="mr-2 h-4 w-4 fill-current" />
              Run Preview & Score Analysis
            </>
          )}
        </Button>
        <div className="flex items-center gap-2 text-xs text-muted-foreground uppercase tracking-widest font-bold opacity-60">
          <BarChart2 className="h-3 w-3" />
          <span>Generates L3 Point-set & L4 metrics</span>
        </div>
      </div>
    </div>
  );
};

export default SelectSamplingStrategy;
