import { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Check, Zap, CircuitBoard, Settings, BarChart3, FileOutput, Cpu } from 'lucide-react';
import { WizardContext } from '../context/WizardContext';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

const steps = [
  { path: 'select-tech', name: 'Technology', icon: Cpu },
  { path: 'select-process-context', name: 'Process', icon: Settings },
  { path: 'select-tool-type', name: 'Metrology', icon: CircuitBoard },
  { path: 'select-sampling-strategy', name: 'Strategy', icon: Zap },
  { path: 'preview-sampling-and-scoring', name: 'Analysis', icon: BarChart3 },
  { path: 'generate-and-review-recipe', name: 'Deployment', icon: FileOutput },
];

const WizardStepper = () => {
  const { state, dispatch } = useContext(WizardContext);
  const navigate = useNavigate();

  const handleNext = () => {
    if (state.currentStep < steps.length) {
      dispatch({ type: 'GO_TO_NEXT_STEP' });
      navigate(`/wizard/${steps[state.currentStep].path}`);
    }
  };

  const handleBack = () => {
    if (state.currentStep > 1) {
      dispatch({ type: 'GO_TO_PREVIOUS_STEP' });
      navigate(`/wizard/${steps[state.currentStep - 2].path}`);
    }
  };

  const progressPercentage = ((state.currentStep - 1) / (steps.length - 1)) * 100;

  return (
    <div className="space-y-8">
      {/* Informational Status Bar */}
      <div className="flex items-center justify-between border-b border-border/50 pb-4 px-1">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-widest text-foreground/80 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
            Workflow Progress
          </h2>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="hidden md:flex flex-col items-end">
            <p className="text-[10px] font-black uppercase tracking-widest text-muted-foreground opacity-60">Completion</p>
            <p className="text-sm font-bold tabular-nums italic">{Math.round(progressPercentage)}%</p>
          </div>
          <div className="h-8 w-px bg-border/50 hidden md:block" />
          <Badge variant="outline" className="h-7 px-3 border-primary/20 bg-primary/5 text-primary font-black italic uppercase text-[10px] tracking-widest">
            Step {state.currentStep} of {steps.length}
          </Badge>
        </div>
      </div>

      {/* Progress Track - Strictly Informational */}
      <div className="grid grid-cols-6 gap-2">
        {steps.map((step, index) => {
          const stepNumber = index + 1;
          const isCompleted = stepNumber < state.currentStep;
          const isCurrent = stepNumber === state.currentStep;
          
          return (
            <div 
              key={step.path} 
              className={`
                relative p-3 rounded-lg border transition-all flex flex-col items-center text-center
                ${isCompleted ? 'bg-muted/30 border-transparent opacity-60' : ''}
                ${isCurrent ? 'bg-background border-primary shadow-sm ring-1 ring-primary/10' : 'bg-muted/10 border-transparent opacity-40'}
              `}
            >
              <div className={`
                flex h-6 w-6 items-center justify-center rounded-full mb-2 text-[10px] font-black transition-colors
                ${isCompleted ? 'bg-success text-success-foreground' : isCurrent ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}
              `}>
                {isCompleted ? <Check className="h-3 w-3" /> : stepNumber}
              </div>
              
              <div className={`font-black text-[9px] uppercase tracking-widest leading-tight ${isCurrent ? 'text-primary' : 'text-muted-foreground'}`}>
                {step.name}
              </div>
              
              {isCurrent && (
                <div className="absolute top-1.5 right-1.5 h-1.5 w-1.5 bg-primary rounded-full animate-pulse" />
              )}
            </div>
          );
        })}
      </div>

      {/* Primary Workflow Navigation */}
      <div className="flex items-center justify-between pt-2">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={state.currentStep === 1 || state.isLoading}
          className="h-10 px-6 border-border/50 hover:bg-muted text-xs font-bold uppercase tracking-widest transition-all active:scale-95"
        >
          <ChevronLeft className="h-3.5 w-3.5 mr-2" /> Previous
        </Button>
        
        <div className="text-[10px] font-black text-muted-foreground/40 uppercase tracking-[0.3em]">
          Stage {state.currentStep} of {steps.length}
        </div>
        
        <Button
          onClick={handleNext}
          disabled={state.currentStep === steps.length || state.isLoading}
          className="h-10 px-8 bg-primary hover:bg-primary/90 text-xs font-bold uppercase tracking-widest shadow-lg shadow-primary/10 transition-all active:scale-95"
        >
          {state.isLoading ? 'Processing...' : 'Continue'} <ChevronRight className="h-3.5 w-3.5 ml-2" />
        </Button>
      </div>
    </div>
  );
};

export default WizardStepper;

