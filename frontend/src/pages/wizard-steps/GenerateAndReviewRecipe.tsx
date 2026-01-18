import { useContext, useState } from 'react';
import { CheckCircle2, Download, FileJson, ChevronDown, ChevronRight, ShieldCheck, FileCheck, Terminal } from 'lucide-react';
import { WizardContext } from '../../context/WizardContext';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { Button } from '../../ui/Button';

const GenerateAndReviewRecipe = () => {
  const { state } = useContext(WizardContext);
  const { toolRecipe, previewWarnings } = state.outputs;
  const [copied, setCopied] = useState(false);
  const [showPayload, setShowPayload] = useState(false);

  const handleExportRecipe = () => {
    if (toolRecipe && toolRecipe.recipe_payload) {
      const json = JSON.stringify(toolRecipe.recipe_payload, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const href = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = href;
      link.download = `sampling-recipe-${toolRecipe.recipe_id}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(href);
    }
  };

  const handleCopyPayload = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (toolRecipe?.recipe_payload) {
      navigator.clipboard.writeText(JSON.stringify(toolRecipe.recipe_payload, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!toolRecipe) return null;

  return (
    <div className="space-y-12 animate-fade-in pb-20">
      {/* Success Hero */}
      <div className="flex flex-col items-center text-center space-y-4 pt-10">
        <div className="h-20 w-20 rounded-full bg-success/10 flex items-center justify-center border-4 border-success/20">
          <CheckCircle2 className="h-10 w-10 text-success" />
        </div>
        <div className="space-y-2">
          <h2 className="text-3xl font-bold tracking-tight">Recipe Generated</h2>
          <p className="text-muted-foreground max-w-sm mx-auto">
            Translation to tool-specific format completed successfully. Review metadata before export.
          </p>
        </div>
      </div>

      <div className="max-w-3xl mx-auto space-y-8">
        {/* Identity & Metadata */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="card-elevated border-primary/20 bg-primary/[0.01]">
            <CardHeader className="pb-3 border-b border-border/50">
              <CardTitle className="text-xs font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                <Terminal className="h-3 w-3" /> System Identifier
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4">
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-primary/60 uppercase">Recipe UID</p>
                <p className="text-lg font-mono font-bold tracking-tight break-all">{toolRecipe.recipe_id}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="card-elevated border-border bg-card">
            <CardHeader className="pb-3 border-b border-border/50">
              <CardTitle className="text-xs font-bold uppercase tracking-widest text-muted-foreground flex items-center gap-2">
                <FileCheck className="h-3 w-3" /> Deployment Profile
              </CardTitle>
            </CardHeader>
            <CardContent className="pt-4 grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-muted-foreground uppercase">Target Tool</p>
                <p className="text-sm font-bold uppercase">{toolRecipe.tool_type}</p>
              </div>
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-muted-foreground uppercase">Format</p>
                <p className="text-sm font-bold font-mono">v{toolRecipe.recipe_format_version}</p>
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Payload Disclosure */}
        <section className="border rounded-xl overflow-hidden bg-card transition-all">
          <button 
            onClick={() => setShowPayload(!showPayload)}
            className="w-full flex items-center justify-between p-5 hover:bg-muted/30 transition-colors"
          >
            <div className="flex items-center gap-3">
              <FileJson className="h-5 w-5 text-muted-foreground" />
              <div className="text-left">
                <p className="font-semibold text-sm">View Recipe Payload</p>
                <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-tight">RAW JSON DATA ({JSON.stringify(toolRecipe.recipe_payload).length} bytes)</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={handleCopyPayload} className="h-8 text-[10px] uppercase font-bold tracking-wider">
                {copied ? 'Copied' : 'Copy JSON'}
              </Button>
              {showPayload ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </div>
          </button>
          
          {showPayload && (
            <div className="border-t bg-slate-950 p-6 overflow-auto max-h-[400px]">
              <pre className="text-[11px] font-mono text-slate-300 leading-relaxed tabular-nums">
                <code>{JSON.stringify(toolRecipe.recipe_payload, null, 2)}</code>
              </pre>
            </div>
          )}
        </section>

        {/* Translation Notes */}
        {((toolRecipe.translation_notes?.length ?? 0) > 0 || previewWarnings.length > 0) && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 px-1">
              <ShieldCheck className="h-4 w-4 text-muted-foreground" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">Validation Notes</h3>
            </div>
            
            <div className="space-y-3">
              {toolRecipe.translation_notes?.map((note, i) => (
                <div key={i} className="flex gap-3 p-4 rounded-lg bg-blue-50/50 border border-blue-100 text-blue-800 text-sm">
                  <div className="h-5 w-5 rounded-full bg-blue-100 flex items-center justify-center shrink-0 text-[10px] font-black">i</div>
                  <p className="leading-relaxed font-medium">{note}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Final Export */}
        <div className="pt-10 flex flex-col items-center">
          <Button
            size="lg"
            onClick={handleExportRecipe}
            className="w-full max-w-md h-16 text-lg font-bold shadow-2xl transition-transform active:scale-[0.98] bg-primary hover:bg-primary/90"
          >
            <Download className="mr-3 h-6 w-6" />
            Download Production Recipe
          </Button>
          <div className="mt-6 flex items-center gap-2 text-[10px] text-muted-foreground uppercase font-black tracking-[0.2em] opacity-40">
            <ShieldCheck className="h-3 w-3" />
            <span>Cryptographically Signed Payload</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GenerateAndReviewRecipe;