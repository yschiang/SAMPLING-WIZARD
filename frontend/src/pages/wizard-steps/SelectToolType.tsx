import { useContext, useEffect, useState } from 'react';
import { Check, Wrench, ShieldCheck, Maximize, Globe, Loader2, AlertCircle } from 'lucide-react';
import { WizardContext } from '../../context/WizardContext';
import { listToolOptions, getToolProfile } from '../../api/catalog';
import type { ToolOption } from '../../api/catalog';
import { Card, CardContent } from '../../ui/Card';
import { Badge } from '../../ui/Badge';

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

  if (!tech || !processContextInputs.processStep) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-in">
        <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-4">
          <Wrench className="h-6 w-6 text-muted-foreground" />
        </div>
        <h2 className="text-xl font-medium">Incomplete Context</h2>
        <p className="text-muted-foreground max-w-xs">Complete process selection to view compatible metrology tools.</p>
      </div>
    );
  }

  return (
    <div className="space-y-10 animate-fade-in max-w-4xl mx-auto">
      {/* Header Section */}
      <div className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">Metrology Selection</h2>
        <p className="text-muted-foreground">
          Select a tool profile compatible with the {processContextInputs.measurementIntent?.toLowerCase()} intent.
        </p>
      </div>

      {state.error && (
        <Card className="border-destructive bg-destructive/5 animate-slide-up">
          <CardContent className="flex items-center gap-3 pt-6">
            <div className="h-10 w-10 rounded-lg bg-destructive/10 flex items-center justify-center">
              <AlertCircle className="h-5 w-5 text-destructive" />
            </div>
            <div>
              <div className="font-semibold text-destructive">Configuration Error</div>
              <div className="text-sm text-destructive/80">{state.error}</div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4">
        {state.isLoading && availableToolOptions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 space-y-3">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <div className="text-center">
                <div className="font-medium">Searching Tools</div>
                <div className="text-sm text-muted-foreground">Finding compatible metrology profiles...</div>
              </div>
            </div>
        ) : (
          availableToolOptions.map((tool) => {
            const isSelected = state.inputs.tool.toolType === tool.tool_type;
            const profile = state.derived.toolProfile;
            
            return (
              <div key={tool.tool_type} className="flex flex-col">
                <button
                  onClick={() => handleSelectTool(tool)}
                  className={`
                    group flex items-center justify-between p-5 rounded-t-xl border transition-all
                    ${isSelected ? 'border-primary bg-primary/[0.02] border-b-transparent' : 'rounded-b-xl hover:bg-muted/50 border-border bg-card'}
                  `}
                >
                  <div className="flex items-center gap-5">
                    <div className={`
                      flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border transition-colors
                      ${isSelected ? 'bg-primary border-primary text-primary-foreground shadow-sm' : 'bg-muted border-transparent'}
                    `}>
                      <Wrench className="h-6 w-6" />
                    </div>
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className={`font-semibold text-lg ${isSelected ? 'text-primary' : 'text-foreground'}`}>
                          {tool.tool_type.replace('_', ' ')}
                        </span>
                        {tool.vendor && (
                          <Badge variant="secondary" className="text-[10px] h-4 px-1.5 font-bold">
                            {tool.vendor}
                          </Badge>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground font-medium uppercase tracking-tight">
                        Model: {tool.model || 'Standard Profile'}
                      </p>
                    </div>
                  </div>
                  <div className={`
                    h-6 w-6 rounded-full border flex items-center justify-center transition-colors
                    ${isSelected ? 'border-primary bg-primary' : 'border-muted-foreground/30'}
                  `}>
                    {isSelected && <Check className="h-4 w-4 text-primary-foreground" />}
                  </div>
                </button>

                {isSelected && profile && (
                  <div className="p-5 bg-muted/30 border-x border-b border-primary rounded-b-xl animate-fade-in grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="flex items-start gap-3">
                      <Maximize className="h-4 w-4 text-primary mt-0.5" />
                      <div>
                        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Grid Capability</p>
                        <p className="text-sm font-medium">{profile.max_points_per_wafer} pts max</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <ShieldCheck className="h-4 w-4 text-primary mt-0.5" />
                      <div>
                        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Edge Support</p>
                        <p className="text-sm font-medium">{profile.edge_die_supported ? 'Full Edge Visibility' : 'Center Only'}</p>
                      </div>
                    </div>
                    <div className="flex items-start gap-3">
                      <Globe className="h-4 w-4 text-primary mt-0.5" />
                      <div>
                        <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider mb-1">Coordinates</p>
                        <p className="text-sm font-medium truncate">{profile.coordinate_system_supported.join(', ')}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default SelectToolType;
