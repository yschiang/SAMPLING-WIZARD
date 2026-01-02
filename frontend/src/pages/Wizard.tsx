import { Outlet } from 'react-router-dom'
import WizardStepper from '../components/WizardStepper'

const Wizard = () => {
  return (
    <div className="space-y-6">
      <WizardStepper />
      <div className="border-t pt-6">
        <Outlet />
      </div>
    </div>
  )
}

export default Wizard
