import { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Check, Zap, CircuitBoard, Settings, BarChart3, FileOutput, Cpu } from 'lucide-react';
import { WizardContext } from '../context/WizardContext';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Card } from '../ui/Card';

const steps = [
  { 
    path: 'select-tech', 
    name: 'Technology Node', 
    short: 'Tech',
    description: 'Select semiconductor technology',
    icon: Cpu
  },
  { 
    path: 'select-process-context', 
    name: 'Process Context', 
    short: 'Process',
    description: 'Define measurement context',
    icon: Settings
  },
  { 
    path: 'select-tool-type', 
    name: 'Tool Selection', 
    short: 'Tools',
    description: 'Choose measurement tools',
    icon: CircuitBoard
  },
  { 
    path: 'select-sampling-strategy', 
    name: 'Sampling Strategy', 
    short: 'Strategy',
    description: 'Configure sampling approach',
    icon: Zap
  },
  { 
    path: 'preview-sampling-and-scoring', 
    name: 'Preview & Analysis', 
    short: 'Preview',
    description: 'Review and score results',
    icon: BarChart3
  },
  { 
    path: 'generate-and-review-recipe', 
    name: 'Recipe Generation', 
    short: 'Recipe',
    description: 'Generate tool recipes',
    icon: FileOutput
  },
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

  const handleStepClick = (stepNumber: number) => {
    if (stepNumber <= state.currentStep) {
      dispatch({ type: 'GO_TO_NEXT_STEP' });
      // Set to the clicked step
      const diff = stepNumber - state.currentStep;
      for (let i = 0; i < Math.abs(diff); i++) {
        if (diff > 0) {
          dispatch({ type: 'GO_TO_NEXT_STEP' });
        } else {
          dispatch({ type: 'GO_TO_PREVIOUS_STEP' });
        }
      }
      navigate(`/wizard/${steps[stepNumber - 1].path}`);
    }
  };

  const progressPercentage = ((state.currentStep - 1) / (steps.length - 1)) * 100;

  return (
    <Card className="card-elevated p-6 space-y-8 animate-slide-up">
      {/* Progress Overview */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="section text-lg">Sampling Workflow</h2>
            <p className="muted">Step {state.currentStep} of {steps.length} • {Math.round(progressPercentage)}% Complete</p>
          </div>
          <Badge variant="secondary" className="mono text-xs px-3 py-1">
            <Zap className="h-3 w-3 mr-1" />
            Active
          </Badge>
        </div>
        
        {/* Progress Bar */}
        <div className="relative">
          <div className="h-2 bg-muted rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-primary transition-all duration-700 ease-out"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Step Navigation - Desktop */}
      <div className="hidden lg:block">
        <div className="grid grid-cols-6 gap-4">
          {steps.map((step, index) => {
            const stepNumber = index + 1;
            const isCompleted = stepNumber < state.currentStep;
            const isCurrent = stepNumber === state.currentStep;
            const isClickable = stepNumber <= state.currentStep;
            const Icon = step.icon;
            
            return (
              <div 
                key={step.path} 
                className={`
                  group relative p-4 rounded-xl border-2 transition-all duration-200
                  ${isClickable ? 'cursor-pointer' : 'cursor-not-allowed'}
                  ${isCompleted 
                    ? 'bg-primary/5 border-primary/30 hover:border-primary/50' 
                    : isCurrent 
                      ? 'bg-accent/5 border-accent shadow-lg ring-2 ring-accent/20'
                      : 'border-muted hover:border-muted-foreground/30'
                  }
                `}
                onClick={() => isClickable && handleStepClick(stepNumber)}
              >
                {/* Step Number/Check */}
                <div className={`
                  flex h-8 w-8 items-center justify-center rounded-lg mb-3 text-xs font-semibold transition-colors
                  ${isCompleted 
                    ? 'bg-primary text-primary-foreground' 
                    : isCurrent 
                      ? 'bg-accent text-accent-foreground'
                      : 'bg-muted text-muted-foreground'
                  }
                `}>
                  {isCompleted ? <Check className="h-4 w-4" /> : stepNumber}
                </div>
                
                {/* Icon */}
                <Icon className={`h-5 w-5 mb-2 transition-colors ${
                  isCurrent ? 'text-accent' : isCompleted ? 'text-primary' : 'text-muted-foreground'
                }`} />
                
                {/* Step Name */}
                <div className={`font-medium text-sm mb-1 ${
                  isCurrent ? 'text-foreground' : 'text-muted-foreground group-hover:text-foreground'
                }`}>
                  {step.short}
                </div>
                
                {/* Description */}
                <div className="text-xs text-muted-foreground line-clamp-2">
                  {step.description}
                </div>
                
                {/* Active Indicator */}
                {isCurrent && (
                  <div className="absolute -top-1 -right-1">
                    <div className="h-3 w-3 bg-accent rounded-full animate-glow" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Step Navigation - Mobile & Tablet */}
      <div className="lg:hidden">
        <div className="flex items-center space-x-4 overflow-x-auto pb-4">
          {steps.map((step, index) => {
            const stepNumber = index + 1;
            const isCompleted = stepNumber < state.currentStep;
            const isCurrent = stepNumber === state.currentStep;
            const Icon = step.icon;
            
            return (
              <div key={step.path} className="flex items-center shrink-0">
                <div className="flex flex-col items-center space-y-2 min-w-[80px]">
                  {/* Step Circle */}
                  <div className={`
                    relative flex h-12 w-12 items-center justify-center rounded-xl border-2 transition-all
                    ${isCompleted 
                      ? 'bg-primary border-primary text-primary-foreground' 
                      : isCurrent 
                        ? 'bg-accent/10 border-accent text-accent ring-2 ring-accent/20'
                        : 'border-muted text-muted-foreground'
                    }
                  `}>
                    {isCompleted ? (
                      <Check className="h-5 w-5" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                    {isCurrent && (
                      <div className="absolute -top-1 -right-1 h-3 w-3 bg-accent rounded-full animate-glow" />
                    )}
                  </div>
                  
                  {/* Step Name */}
                  <div className="text-center">
                    <div className={`text-xs font-medium ${
                      isCurrent ? 'text-foreground' : 'text-muted-foreground'
                    }`}>
                      {step.short}
                    </div>
                  </div>
                </div>
                
                {/* Connector Line */}
                {index < steps.length - 1 && (
                  <div className={`h-0.5 w-8 mx-3 transition-colors ${
                    isCompleted ? 'bg-primary' : 'bg-muted'
                  }`} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Current Step Info */}
      <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg border">
        <div className="flex items-center space-x-3">
          {(() => {
            const CurrentIcon = steps[state.currentStep - 1].icon;
            return <CurrentIcon className="h-5 w-5 text-accent" />;
          })()}
          <div>
            <div className="font-semibold text-sm">{steps[state.currentStep - 1].name}</div>
            <div className="text-xs text-muted-foreground">{steps[state.currentStep - 1].description}</div>
          </div>
        </div>
      </div>

      {/* Navigation Buttons */}
      <div className="flex items-center justify-between pt-6 border-t">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={state.currentStep === 1}
          className="flex items-center gap-2 px-6"
        >
          <ChevronLeft className="h-4 w-4" />
          Previous
        </Button>
        
        <div className="flex items-center space-x-2 text-sm text-muted-foreground mono">
          <span>{state.currentStep}</span>
          <span>/</span>
          <span>{steps.length}</span>
        </div>
        
        <Button
          onClick={handleNext}
          disabled={state.currentStep === steps.length}
          className="flex items-center gap-2 px-6 bg-gradient-primary hover:opacity-90"
        >
          {state.currentStep === steps.length ? 'Complete' : 'Continue'}
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>
    </Card>
  );
};

export default WizardStepper;
