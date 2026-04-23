
import { clsx } from 'clsx';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'secondary' | 'white';
  className?: string;
  text?: string;
}

const sizeClasses = {
  sm: 'w-6 h-6',
  md: 'w-10 h-10',
  lg: 'w-14 h-14',
};

const colorClasses = {
  primary: 'border-primary-600',
  secondary: 'border-gray-600',
  white: 'border-white',
};

export function LoadingSpinner({ 
  size = 'md', 
  color = 'primary', 
  className,
  text
}: LoadingSpinnerProps) {
  return (
    <div className={clsx('flex items-center justify-center', className)}>
      <div className="flex flex-col items-center space-y-4">
        <div
          className={clsx(
            'border-4 border-gray-200 border-t-transparent rounded-full animate-spin',
            sizeClasses[size],
            colorClasses[color]
          )}
          role="status"
          aria-label="Loading"
        >
          <span className="sr-only">Loading...</span>
        </div>
        {text && (
          <p className="text-base text-gray-700 animate-pulse">{text}</p>
        )}
      </div>
    </div>
  );
}

// Full page loading component
export function PageLoading({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="fixed inset-0 bg-white bg-opacity-90 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-lg p-8 max-w-sm w-full mx-4">
        <LoadingSpinner size="lg" text={message} className="py-4" />
      </div>
    </div>
  );
}

// Inline loading for buttons
export function ButtonSpinner({ className = '' }: { className?: string }) {
  return (
    <div className={clsx('w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin', className)} />
  );
}
