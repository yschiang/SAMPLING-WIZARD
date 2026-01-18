import { useContext, useEffect, useState } from 'react';
import { Check, Cpu, CircuitBoard } from 'lucide-react';
import { WizardContext } from '../../context/WizardContext';
import { listTechs, listWaferMaps, getWaferMapSpec } from '../../api/catalog';
import type { WaferMapSummary } from '../../api/catalog';

const SelectTech = () => {
  const { state, dispatch } = useContext(WizardContext);
  const [availableTechs, setAvailableTechs] = useState<string[]>([]);
  const [availableWaferMaps, setAvailableWaferMaps] = useState<WaferMapSummary[]>([]);

  // Fetch Techs on mount
  useEffect(() => {
    const fetchTechs = async () => {
      dispatch({ type: 'SET_LOADING', payload: true });
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
    <div className="space-y-10 animate-fade-in max-w-3xl mx-auto">
      {/* Header Section */}
      <div className="space-y-2">
        <h2 className="text-2xl font-semibold tracking-tight">Technology Node</h2>
        <p className="text-muted-foreground">
          Define the semiconductor process technology and base wafer geometry.
        </p>
      </div>

      <div className="space-y-12">
        {/* Tech Selection */}
        <section className="space-y-4">
          <div className="grid gap-3">
            {availableTechs.map((tech) => {
              const isSelected = state.inputs.tech === tech;
              return (
                <button
                  key={tech}
                  onClick={() => handleSelectTech(tech)}
                  className={`
                    group flex items-center justify-between p-4 rounded-lg border text-left transition-all
                    ${isSelected ? 'border-primary ring-1 ring-primary bg-primary/[0.02]' : 'hover:bg-muted/50 border-border'}
                  `}
                >
                  <div className="flex items-center gap-4">
                    <div className={`
                      flex h-10 w-10 shrink-0 items-center justify-center rounded-md border transition-colors
                      ${isSelected ? 'bg-primary border-primary text-primary-foreground' : 'bg-muted border-transparent group-hover:border-border'}
                    `}>
                      <Cpu className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="font-medium">{tech}</div>
                      <div className="text-xs text-muted-foreground uppercase tracking-wider">Process Node</div>
                    </div>
                  </div>
                  <div className={`
                    h-5 w-5 rounded-full border flex items-center justify-center transition-colors
                    ${isSelected ? 'border-primary bg-primary' : 'border-muted-foreground/30'}
                  `}>
                    {isSelected && <Check className="h-3 w-3 text-primary-foreground" />}
                  </div>
                </button>
              );
            })}
          </div>
        </section>

        {/* Wafer Map Selection (Progressive Disclosure) */}
        {state.inputs.tech && (
          <section className="space-y-6 pt-6 border-t animate-fade-in">
            <div className="space-y-1">
              <h3 className="text-lg font-medium">Wafer Map Configuration</h3>
              <p className="text-sm text-muted-foreground">Select the layout defining die coordinates and boundaries.</p>
            </div>
            
            <div className="grid gap-3">
              {availableWaferMaps.map((map) => {
                const isSelected = state.inputs.waferMapId === map.wafer_map_id;
                return (
                  <button
                    key={map.wafer_map_id}
                    onClick={() => handleSelectWaferMap(map.wafer_map_id)}
                    className={`
                      group flex items-center justify-between p-4 rounded-lg border text-left transition-all
                      ${isSelected ? 'border-primary ring-1 ring-primary bg-primary/[0.02]' : 'hover:bg-muted/50 border-border'}
                    `}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`
                        flex h-10 w-10 shrink-0 items-center justify-center rounded-md border transition-colors
                        ${isSelected ? 'bg-primary border-primary text-primary-foreground' : 'bg-muted border-transparent group-hover:border-border'}
                      `}>
                        <CircuitBoard className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="font-medium uppercase tracking-tight">{map.wafer_map_id}</div>
                        <div className="text-xs text-muted-foreground">{map.description}</div>
                      </div>
                    </div>
                    <div className={`
                      h-5 w-5 rounded-full border flex items-center justify-center transition-colors
                      ${isSelected ? 'border-primary bg-primary' : 'border-muted-foreground/30'}
                    `}>
                      {isSelected && <Check className="h-3 w-3 text-primary-foreground" />}
                    </div>
                  </button>
                );
              })}
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

export default SelectTech;

