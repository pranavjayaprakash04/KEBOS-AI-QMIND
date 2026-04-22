// Simple test file to verify react-hot-toast works
import toast from 'react-hot-toast';

console.log('react-hot-toast imported successfully:', typeof toast);

export const testToast = () => {
  toast.success('Test toast notification!');
};
