import { Outlet } from 'react-router-dom'
import WizardStepper from '../components/WizardStepper'

const Wizard = () => {
  return (
    <div className="space-y-12">
      <WizardStepper />
      <main className="animate-fade-in px-1">
        <Outlet />
      </main>
    </div>
  )
}

export default Wizard
