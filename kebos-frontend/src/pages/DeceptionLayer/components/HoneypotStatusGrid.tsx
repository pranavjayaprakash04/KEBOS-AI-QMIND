import React from 'react'
import { TrapType, TrapStatus } from '../../../types/deception'
import { useAuthStore } from '../../../store/authStore'

interface HoneypotStatusGridProps {
  traps: TrapStatus[]
  onStart: (type: TrapType) => void
}

const TRAP_CONFIG: Record<TrapType, { name: string; color: string; icon: string }> = {
  ssh: { name: 'SSH Trap', color: 'blue', icon: '🔒' },
  http: { name: 'HTTP Trap', color: 'amber', icon: '🌐' },
  rdp: { name: 'RDP Trap', color: 'purple', icon: '🖥️' },
}

export const HoneypotStatusGrid: React.FC<HoneypotStatusGridProps> = ({
  traps,
  onStart,
}) => {
  const { user } = useAuthStore()
  const canStart = user?.role === 'ADMIN' || user?.role === 'ANALYST' || user?.role === 'admin' || user?.role === 'analyst'

  return (
    <div className="space-y-4">
      {traps.map((trap) => {
        const config = TRAP_CONFIG[trap.trap_type]
        const isRunning = trap.running

        return (
          <div
            key={trap.trap_type}
            className={`bg-white rounded-lg shadow-md p-4 border-l-4 ${
              isRunning ? `border-${config.color}-500` : 'border-red-500'
            }`}
          >
            <div className="flex justify-between items-start">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xl">{config.icon}</span>
                  <h3 className="font-semibold text-gray-800">{config.name}</h3>
                </div>
                <p className="text-sm text-gray-500 mt-1">Port {trap.port}</p>
              </div>

              <div className="flex items-center gap-2">
                <span
                  className={`inline-block w-3 h-3 rounded-full ${
                    isRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                  }`}
                />
                <span className={`text-sm font-medium ${isRunning ? 'text-green-600' : 'text-red-600'}`}>
                  {isRunning ? 'Active' : 'Offline'}
                </span>
              </div>
            </div>

            <div className="mt-4">
              <div className="text-3xl font-bold text-gray-800">
                {trap.hit_count.toLocaleString()}
              </div>
              <p className="text-xs text-gray-500">hits detected</p>
            </div>

            {!isRunning && canStart && (
              <button
                onClick={() => onStart(trap.trap_type)}
                className={`mt-3 w-full py-2 px-4 bg-${config.color}-600 hover:bg-${config.color}-700 text-white rounded font-medium transition-colors`}
              >
                Start {config.name}
              </button>
            )}
          </div>
        )
      })}
    </div>
  )
}

export default HoneypotStatusGrid
