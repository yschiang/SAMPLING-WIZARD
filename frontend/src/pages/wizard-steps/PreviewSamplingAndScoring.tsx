import WaferMap from '../../components/WaferMap/WaferMap';
import { generateRecipe } from '../../api/catalog';
import { Card, CardContent } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/Table';
import { Alert, AlertDescription, AlertTitle } from '../../ui/Alert';

const PreviewSamplingAndScoring = () => {
  const { state, dispatch } = useContext(WizardContext);
  const navigate = useNavigate();

  const { waferMapSpec, toolProfile } = state.derived;
  const { samplingOutput, previewWarnings, scoreReport } = state.outputs;

  const handleGenerateRecipe = async () => {
    if (!waferMapSpec || !toolProfile || !samplingOutput) {
      dispatch({ type: 'SET_ERROR', payload: 'Required analysis data missing.' });
      return;
    }

    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      const response = await generateRecipe({
        wafer_map_spec: waferMapSpec,
        tool_profile: toolProfile,
        sampling_output: samplingOutput,
        ...(scoreReport && { score_report: scoreReport }),
      });
      dispatch({ type: 'SET_RECIPE_OUTPUT', payload: response.tool_recipe });
      navigate('/wizard/generate-and-review-recipe');
    } catch (err: any) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  if (!samplingOutput) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-in">
        <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mb-4">
          <Map className="h-6 w-6 text-muted-foreground" />
        </div>
        <h2 className="text-xl font-medium">No Analysis Results</h2>
        <p className="text-muted-foreground max-w-xs mb-6">Return to strategy selection to run analysis.</p>
        <Button variant="outline" onClick={() => navigate('/wizard/select-sampling-strategy')}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Strategy
        </Button>
      </div>
    );
  }

  const getScoreStatus = (score: number) => {
    if (score >= 0.8) return { label: 'Optimal', color: 'bg-success', text: 'text-success' };
    if (score >= 0.6) return { label: 'Acceptable', color: 'bg-primary', text: 'text-primary' };
    return { label: 'Suboptimal', color: 'bg-warning', text: 'text-warning' };
  };

  return (
    <div className="space-y-10 animate-fade-in">
      {/* Header */}
      <div className="flex items-end justify-between border-b pb-6">
        <div className="space-y-1">
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">Preview & Analysis</h2>
          <p className="text-sm text-muted-foreground">Spatial distribution validation and quality metrics.</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="px-3 py-1 bg-muted/50 font-mono text-xs">
            Points: {samplingOutput.selected_points.length}
          </Badge>
          <Badge variant="outline" className="px-3 py-1 bg-muted/50 font-mono text-xs uppercase">
            {state.inputs.strategy.strategyId}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
        {/* Visualization - PRIMARY */}
        <div className="xl:col-span-7 space-y-6">
          <Card className="card-elevated overflow-hidden bg-white">
            <CardContent className="p-6 min-h-[500px] flex flex-col">
              {waferMapSpec && (
                <WaferMap 
                  waferMapSpec={waferMapSpec} 
                  samplingOutput={samplingOutput}
                  className="flex-1 w-full"
                />
              )}
            </CardContent>
          </Card>
          
          {previewWarnings.length > 0 && (
            <Alert className="bg-amber-50/50 border-amber-200">
              <AlertTriangle className="h-4 w-4 text-amber-600" />
              <AlertTitle className="text-amber-800 text-xs font-bold uppercase tracking-wider">Analysis Warning</AlertTitle>
              <AlertDescription className="text-amber-700 text-sm">
                The sampling engine reported {previewWarnings.length} non-blocking advisory issue(s).
              </AlertDescription>
            </Alert>
          )}
        </div>

        {/* Interpretation - RIGHT PANEL */}
        <div className="xl:col-span-5 space-y-8">
          {/* Metrics */}
          <section className="space-y-6">
            <div className="flex items-center gap-2 px-1">
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Quality Interpretation</h3>
            </div>

            {scoreReport ? (
              <div className="space-y-8">
                {/* Overall Hero */}
                <div className="flex items-center justify-between p-5 rounded-xl border bg-card shadow-sm">
                  <div>
                    <div className="text-xs font-bold text-muted-foreground uppercase tracking-tighter mb-1">Composite Score</div>
                    <div className={`text-sm font-bold ${getScoreStatus(scoreReport.overall_score).text} uppercase tracking-widest`}>
                      {getScoreStatus(scoreReport.overall_score).label}
                    </div>
                  </div>
                  <div className="text-5xl font-bold tracking-tighter tabular-nums">
                    {(scoreReport.overall_score * 100).toFixed(0)}<span className="text-lg text-muted-foreground ml-0.5">%</span>
                  </div>
                </div>

                {/* Detailed Bars */}
                <div className="space-y-5 px-1">
                  {[
                    { label: 'Spatial Coverage', value: scoreReport.coverage_score },
                    { label: 'Statistical Confidence', value: scoreReport.statistical_score },
                    { label: 'Risk Alignment', value: scoreReport.risk_alignment_score },
                  ].map((m) => (
                    <div key={m.label} className="space-y-2">
                      <div className="flex justify-between text-xs font-medium">
                        <span className="text-muted-foreground">{m.label}</span>
                        <span className="tabular-nums">{(m.value * 100).toFixed(0)}%</span>
                      </div>
                      <div className="h-1.5 w-full bg-muted rounded-full overflow-hidden">
                        <div 
                          className={`h-full transition-all duration-1000 ${getScoreStatus(m.value).color}`} 
                          style={{ width: `${m.value * 100}%` }} 
                        />
                      </div>
                    </div>
                  ))}
                </div>

                {/* Score Warnings */}
                {scoreReport.warnings.length > 0 && (
                  <div className="space-y-2">
                    {scoreReport.warnings.map((w, i) => (
                      <div key={i} className="flex gap-2 text-[11px] leading-tight text-amber-700 font-medium bg-amber-50/50 p-2 rounded border border-amber-100">
                        <AlertTriangle className="h-3 w-3 shrink-0 mt-0.5" />
                        <span><span className="font-bold">{w.code}:</span> {w.message}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="py-12 text-center text-muted-foreground text-sm italic">Analysis metrics unavailable.</div>
            )}
          </section>

          {/* Coordinates - SECONDARY */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 px-1">
              <List className="h-4 w-4 text-muted-foreground" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Coordinates List</h3>
            </div>
            <div className="border rounded-lg overflow-hidden bg-card">
              <div className="h-[200px] overflow-auto">
                <Table>
                  <TableHeader className="sticky top-0 bg-muted/50 z-10">
                    <TableRow className="h-8">
                      <TableHead className="h-8 text-[10px] uppercase font-bold text-muted-foreground pl-4">Index</TableHead>
                      <TableHead className="h-8 text-[10px] uppercase font-bold text-muted-foreground text-center">Die X</TableHead>
                      <TableHead className="h-8 text-[10px] uppercase font-bold text-muted-foreground text-center pr-4">Die Y</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {samplingOutput.selected_points.map((p, i) => (
                      <TableRow key={i} className="h-8 hover:bg-muted/30 transition-colors border-border/50">
                        <TableCell className="py-0 text-[10px] font-mono text-muted-foreground/60 pl-4">#{String(i + 1).padStart(2, '0')}</TableCell>
                        <TableCell className="py-0 text-xs font-mono font-medium text-center">{p.die_x}</TableCell>
                        <TableCell className="py-0 text-xs font-mono font-medium text-center pr-4">{p.die_y}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          </section>
        </div>
      </div>

      {/* CTA */}
      <div className="flex flex-col items-center pt-12 border-t">
        <Button
          size="lg"
          onClick={handleGenerateRecipe}
          disabled={state.isLoading || !samplingOutput}
          className="w-full max-w-md h-14 text-base font-semibold shadow-xl transition-transform active:scale-[0.98]"
        >
          {state.isLoading ? (
            <>
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Generating Recipe...
            </>
          ) : (
            <>
              <FileCode className="mr-2 h-5 w-5" />
              Finalize & Generate Tool Recipe
            </>
          )}
        </Button>
        <p className="mt-4 text-xs text-muted-foreground font-medium flex items-center gap-2">
          <Check className="h-3.5 w-3.5 text-success" /> Validated coordinate-set ready for tool translation.
        </p>
      </div>
    </div>
  );
};

export default PreviewSamplingAndScoring;

