import { Routes, Route, Navigate } from 'react-router-dom'
import { Cpu, Zap } from 'lucide-react'
import { ThemeProvider } from './components/ThemeProvider'
import { WizardProvider } from './context/WizardContext'
import Wizard from './pages/Wizard'
import SelectTech from './pages/wizard-steps/SelectTech'
import SelectProcessContext from './pages/wizard-steps/SelectProcessContext'
import SelectToolType from './pages/wizard-steps/SelectToolType'
import SelectSamplingStrategy from './pages/wizard-steps/SelectSamplingStrategy'
import PreviewSamplingAndScoring from './pages/wizard-steps/PreviewSamplingAndScoring'
import GenerateAndReviewRecipe from './pages/wizard-steps/GenerateAndReviewRecipe'

function App() {
  return (
    <ThemeProvider defaultTheme="light" storageKey="sampling-wizard-theme">
      <div className="min-h-screen bg-background relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 circuit-pattern opacity-40" />
        
        {/* Header */}
        <header className="relative border-b glass backdrop-blur-md">
          <div className="page-container py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="h-10 w-10 rounded-lg bg-gradient-primary flex items-center justify-center shadow-lg">
                    <Cpu className="h-5 w-5 text-white" />
                  </div>
                  <div className="absolute -top-1 -right-1 h-3 w-3 bg-accent rounded-full animate-glow" />
                </div>
                <div>
                  <h1 className="title text-2xl md:text-3xl">Sampling Wizard</h1>
                  <p className="muted text-sm">Advanced Semiconductor Wafer Analysis</p>
                </div>
              </div>
              
              <div className="flex items-center space-x-2">
                <div className="hidden md:flex items-center space-x-1 text-xs mono text-muted-foreground bg-muted/50 px-3 py-1.5 rounded-full">
                  <Zap className="h-3 w-3 text-accent" />
                  <span>v1.0.0</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="relative">
          <div className="page-container animate-fade-in">
            <WizardProvider>
              <Routes>
                <Route path="/" element={<Navigate to="/wizard" replace />} />
                <Route path="/wizard" element={<Wizard />}>
                  <Route index element={<Navigate to="select-tech" replace />} />
                  <Route path="select-tech" element={<SelectTech />} />
                  <Route path="select-process-context" element={<SelectProcessContext />} />
                  <Route path="select-tool-type" element={<SelectToolType />} />
                  <Route path="select-sampling-strategy" element={<SelectSamplingStrategy />} />
                  <Route path="preview-sampling-and-scoring" element={<PreviewSamplingAndScoring />} />
                  <Route path="generate-and-review-recipe" element={<GenerateAndReviewRecipe />} />
                </Route>
              </Routes>
            </WizardProvider>
          </div>
        </main>

        {/* Footer */}
        <footer className="relative border-t glass backdrop-blur-md mt-12">
          <div className="page-container py-6">
            <div className="flex flex-col md:flex-row items-center justify-between space-y-2 md:space-y-0">
              <p className="muted text-sm">
                Semiconductor sampling optimization platform
              </p>
              <div className="flex items-center space-x-4 text-sm">
                <span className="muted">Powered by advanced algorithms</span>
                <div className="h-1.5 w-1.5 bg-primary rounded-full animate-glow" />
                <span className="muted">Real-time analysis</span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </ThemeProvider>
  )
}

export default App
