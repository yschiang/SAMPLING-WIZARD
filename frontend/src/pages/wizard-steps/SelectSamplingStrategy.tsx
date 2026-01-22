import { useContext, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Check, Play, BarChart2, Info, Sliders, AlertCircle } from 'lucide-react';
import { WizardContext } from '../../context/WizardContext';
import { previewSampling, scoreSampling } from '../../api/catalog';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { StrategyPreview } from '../../components/StrategyPreview';

const strategyDescriptions: Record<string, string> = {
  'CENTER_EDGE': 'Balances center process control with edge exclusion monitoring. Ideal for standard lithography checks.',
  'GRID_UNIFORM': 'Uniform grid distribution for baseline process characterization and full-wafer uniformity mapping.',
  'EDGE_ONLY': 'Concentrated sampling on the wafer perimeter. Critical for detecting clamp, bevel, and handling defects.',
  'ZONE_RING_N': 'Concentric multi-zone sampling. Best for processes with radial variation signatures like CVD or CMP.',
};

const SelectSamplingStrategy = () => {
  const { state, dispatch } = useContext(WizardContext);
  const navigate = useNavigate();

  const { strategyId, strategy_config } = state.inputs.strategy;
  const commonParams = strategy_config?.common;

  // Ensure default params are set on selection (handled by reducer now, but safety check)
  useEffect(() => {
    if (strategyId && !commonParams) {
      dispatch({
        type: 'SET_STRATEGY_PARAMS',
        payload: {
          edge_exclusion_mm: 5,
          target_point_count: 100,
          rotation_seed: 0
        }
      });
    }
  }, [strategyId, commonParams, dispatch]);

  const handleSelectStrategy = (id: string) => {
    dispatch({ type: 'SET_STRATEGY', payload: id });
  };

  const handleParamChange = (key: string, value: string) => {
    const numValue = parseFloat(value);
    dispatch({
      type: 'SET_STRATEGY_PARAMS',
      payload: { [key]: isNaN(numValue) ? 0 : numValue }
    });
  };

  const handlePreviewAndScore = async () => {
    const { waferMapSpec, processContext, toolProfile } = state.derived;

    if (!waferMapSpec || !processContext || !toolProfile || !strategyId) {
      dispatch({
        type: 'SET_ERROR',
        payload: 'Cannot run preview. Missing required configuration context.',
      });
      return;
    }

    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      // v1.3 API: Pass strategy_config instead of params
      const previewResponse = await previewSampling({
        wafer_map_spec: waferMapSpec,
        process_context: processContext,
        tool_profile: toolProfile,
        strategy: { 
          strategy_id: strategyId,
          strategy_config: strategy_config
        },
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
          const isSelected = strategyId === strategy;
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
                    {strategyDescriptions[strategy] || 'Advanced sampling algorithm.'}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Configuration Panel */}
      {strategyId && (
        <Card className="card-elevated animate-fade-in border-l-4 border-l-primary">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-2 text-base">
              <Sliders className="h-4 w-4 text-primary" />
              Strategy Configuration
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Target Point Count</label>
                <Input 
                  type="number" 
                  min="1" 
                  max="1000"
                  value={commonParams?.target_point_count ?? 100}
                  onChange={(e) => handleParamChange('target_point_count', e.target.value)}
                  className="font-mono"
                />
                <p className="text-[10px] text-muted-foreground">Total sampling points (approximate)</p>
              </div>
              
              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Edge Exclusion (mm)</label>
                <Input 
                  type="number" 
                  min="0" 
                  max="500"
                  value={commonParams?.edge_exclusion_mm ?? 5}
                  onChange={(e) => handleParamChange('edge_exclusion_mm', e.target.value)}
                  className="font-mono"
                />
                <p className="text-[10px] text-muted-foreground">Margin from wafer edge</p>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Rotation Seed</label>
                <Input 
                  type="number" 
                  value={commonParams?.rotation_seed ?? 0}
                  onChange={(e) => handleParamChange('rotation_seed', e.target.value)}
                  className="font-mono"
                />
                <p className="text-[10px] text-muted-foreground">Randomization seed for reproducibility</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {state.error && (
        <div className="rounded-lg bg-destructive/10 border border-destructive/20 p-4 flex items-center gap-3 animate-fade-in">
          <AlertCircle className="h-5 w-5 text-destructive" />
          <p className="text-sm font-medium text-destructive">{state.error}</p>
        </div>
      )}

      {/* CTA Section */}
      <div className="flex flex-col items-center pt-8 space-y-4 border-t border-border/40">
        <Button
          size="lg"
          onClick={handlePreviewAndScore}
          disabled={state.isLoading || !strategyId}
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
