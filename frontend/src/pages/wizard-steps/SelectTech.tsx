import { useContext, useEffect, useState } from 'react';
import { Loader2, AlertCircle, Check, Cpu, CircuitBoard } from 'lucide-react';
import { WizardContext } from '../../context/WizardContext';
import { listTechs, listWaferMaps, getWaferMapSpec } from '../../api/catalog';
import type { WaferMapSummary } from '../../api/catalog';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';

const SelectTech = () => {
  const { state, dispatch } = useContext(WizardContext);
  const [availableTechs, setAvailableTechs] = useState<string[]>([]);
  const [availableWaferMaps, setAvailableWaferMaps] = useState<WaferMapSummary[]>([]);

  // Fetch Techs on mount
  useEffect(() => {
    const fetchTechs = async () => {
      dispatch({ type: 'SET_LOADING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });
      try {
        const response = await listTechs();
        setAvailableTechs(response.techs);
      } catch (err: any) {
        dispatch({ type: 'SET_ERROR', payload: err.message });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };
    fetchTechs();
  }, [dispatch]);

  // Fetch Wafer Maps when tech changes
  useEffect(() => {
    if (state.inputs.tech) {
      const fetchWaferMaps = async () => {
        dispatch({ type: 'SET_LOADING', payload: true });
        dispatch({ type: 'SET_ERROR', payload: null });
        try {
          const response = await listWaferMaps(state.inputs.tech!);
          setAvailableWaferMaps(response.wafer_maps);
        } catch (err: any) {
          dispatch({ type: 'SET_ERROR', payload: err.message });
        } finally {
          dispatch({ type: 'SET_LOADING', payload: false });
        }
      };
      fetchWaferMaps();
    } else {
      setAvailableWaferMaps([]);
    }
  }, [state.inputs.tech, dispatch]);

  const handleSelectTech = (tech: string) => {
    dispatch({ type: 'SET_TECH', payload: tech });
  };

  const handleSelectWaferMap = async (waferMapId: string) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });
    try {
      const spec = await getWaferMapSpec(waferMapId);
      dispatch({ type: 'SET_WAFER_MAP', payload: { id: waferMapId, spec } });
    } catch (err: any) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header Section */}
      <div className="text-center space-y-3">
        <h2 className="section text-2xl">Technology Configuration</h2>
        <p className="muted max-w-2xl mx-auto">
          Configure your semiconductor technology node and wafer mapping parameters for optimal sampling analysis.
        </p>
      </div>

      {/* Error Display */}
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

      <div className="page-grid">
        {/* Tech Selection */}
        <div className="col-span-12 lg:col-span-6">
          <Card className="card-elevated card-interactive h-full">
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-3">
                <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                  <Cpu className="h-4 w-4 text-primary" />
                </div>
                Technology Node
                {state.inputs.tech && (
                  <div className="ml-auto">
                    <Badge variant="default" className="bg-success text-success-foreground">
                      <Check className="h-3 w-3 mr-1" />
                      Selected
                    </Badge>
                  </div>
                )}
              </CardTitle>
              <CardDescription className="text-base">
                Choose the semiconductor process technology for your wafer analysis.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {state.inputs.tech && (
                <div className="p-4 bg-primary/5 rounded-lg border border-primary/20">
                  <div className="flex items-center gap-3">
                    <div className="h-6 w-6 rounded bg-primary/10 flex items-center justify-center">
                      <Check className="h-3 w-3 text-primary" />
                    </div>
                    <div>
                      <div className="font-semibold">{state.inputs.tech}</div>
                      <div className="text-sm text-muted-foreground">Active technology node</div>
                    </div>
                  </div>
                </div>
              )}
              
              {state.isLoading ? (
                <div className="flex flex-col items-center justify-center py-12 space-y-3">
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  <div className="text-center">
                    <div className="font-medium">Loading Technologies</div>
                    <div className="text-sm text-muted-foreground">Fetching available process nodes...</div>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {availableTechs.map((tech) => {
                    const isSelected = state.inputs.tech === tech;
                    return (
                      <Button
                        key={tech}
                        variant={isSelected ? "default" : "outline"}
                        onClick={() => handleSelectTech(tech)}
                        disabled={state.isLoading}
                        className={`
                          h-16 p-4 flex flex-col items-center justify-center space-y-1 transition-all duration-200
                          ${isSelected ? 'bg-gradient-primary text-white shadow-lg' : 'hover:border-primary/50 hover:bg-primary/5'}
                        `}
                      >
                        <div className="font-semibold">{tech}</div>
                        <div className="text-xs opacity-80">Process Node</div>
                      </Button>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Wafer Map Selection */}
        <div className="col-span-12 lg:col-span-6">
          <Card className={`card-elevated h-full transition-all duration-300 ${
            state.inputs.tech ? 'card-interactive' : 'opacity-60'
          }`}>
            <CardHeader className="pb-4">
              <CardTitle className="flex items-center gap-3">
                <div className={`h-8 w-8 rounded-lg flex items-center justify-center transition-colors ${
                  state.inputs.tech ? 'bg-accent/10' : 'bg-muted'
                }`}>
                  <CircuitBoard className={`h-4 w-4 ${
                    state.inputs.tech ? 'text-accent' : 'text-muted-foreground'
                  }`} />
                </div>
                Wafer Map Configuration
                {state.inputs.waferMapId && (
                  <div className="ml-auto">
                    <Badge variant="default" className="bg-success text-success-foreground">
                      <Check className="h-3 w-3 mr-1" />
                      Configured
                    </Badge>
                  </div>
                )}
              </CardTitle>
              <CardDescription className="text-base">
                {state.inputs.tech 
                  ? "Select the wafer layout that defines die coordinates and boundaries."
                  : "Please select a technology node first to configure wafer mapping."
                }
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!state.inputs.tech ? (
                <div className="flex flex-col items-center justify-center py-12 space-y-3 text-center">
                  <div className="h-12 w-12 rounded-lg bg-muted/50 flex items-center justify-center">
                    <CircuitBoard className="h-6 w-6 text-muted-foreground" />
                  </div>
                  <div>
                    <div className="font-medium text-muted-foreground">Awaiting Technology Selection</div>
                    <div className="text-sm text-muted-foreground">Choose a tech node to proceed</div>
                  </div>
                </div>
              ) : (
                <>
                  {state.inputs.waferMapId && (
                    <div className="p-4 bg-accent/5 rounded-lg border border-accent/20">
                      <div className="flex items-center gap-3">
                        <div className="h-6 w-6 rounded bg-accent/10 flex items-center justify-center">
                          <Check className="h-3 w-3 text-accent" />
                        </div>
                        <div>
                          <div className="font-semibold">{state.inputs.waferMapId}</div>
                          <div className="text-sm text-muted-foreground">Active wafer configuration</div>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {state.isLoading ? (
                    <div className="flex flex-col items-center justify-center py-12 space-y-3">
                      <Loader2 className="h-8 w-8 animate-spin text-accent" />
                      <div className="text-center">
                        <div className="font-medium">Loading Wafer Maps</div>
                        <div className="text-sm text-muted-foreground">Fetching compatible configurations...</div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {availableWaferMaps.map((map) => {
                        const isSelected = state.inputs.waferMapId === map.wafer_map_id;
                        return (
                          <Card 
                            key={map.wafer_map_id}
                            className={`
                              cursor-pointer transition-all duration-200 hover:shadow-md
                              ${isSelected 
                                ? 'ring-2 ring-accent bg-accent/5 border-accent/30' 
                                : 'hover:border-accent/30 hover:bg-accent/5'
                              }
                            `}
                            onClick={() => handleSelectWaferMap(map.wafer_map_id)}
                          >
                            <CardContent className="p-4">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <div className={`h-8 w-8 rounded-lg border-2 flex items-center justify-center transition-colors ${
                                    isSelected 
                                      ? 'bg-accent border-accent text-accent-foreground' 
                                      : 'border-muted-foreground/30 text-muted-foreground'
                                  }`}>
                                    {isSelected ? (
                                      <Check className="h-4 w-4" />
                                    ) : (
                                      <CircuitBoard className="h-4 w-4" />
                                    )}
                                  </div>
                                  <div>
                                    <div className="font-semibold">{map.wafer_map_id}</div>
                                    <div className="text-sm text-muted-foreground">{map.description}</div>
                                  </div>
                                </div>
                                {isSelected && (
                                  <div className="h-2 w-2 bg-accent rounded-full animate-glow" />
                                )}
                              </div>
                            </CardContent>
                          </Card>
                        );
                      })}
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Summary Card */}
      {(state.inputs.tech || state.inputs.waferMapId) && (
        <Card className="card-elevated animate-slide-up">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-lg bg-gradient-primary flex items-center justify-center">
                  <Cpu className="h-6 w-6 text-white" />
                </div>
                <div>
                  <div className="font-semibold">Configuration Summary</div>
                  <div className="text-sm text-muted-foreground">
                    {state.inputs.tech && state.inputs.waferMapId 
                      ? "Technology and wafer mapping configured"
                      : "Partial configuration - please complete all selections"
                    }
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                {state.inputs.tech && (
                  <div className="text-right">
                    <div className="text-sm font-medium">{state.inputs.tech}</div>
                    <div className="text-xs text-muted-foreground">Technology</div>
                  </div>
                )}
                {state.inputs.waferMapId && (
                  <div className="text-right">
                    <div className="text-sm font-medium">{state.inputs.waferMapId}</div>
                    <div className="text-xs text-muted-foreground">Wafer Map</div>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SelectTech;
