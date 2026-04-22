// Simple test to verify imports work
console.log('Testing module imports...');

// Test react-hot-toast
try {
  const toast = require('react-hot-toast');
  console.log('✅ react-hot-toast imported successfully');
} catch (error) {
  console.log('❌ react-hot-toast import failed:', error.message);
}

// Test @tanstack/react-query
try {
  const reactQuery = require('@tanstack/react-query');
  console.log('✅ @tanstack/react-query imported successfully');
} catch (error) {
  console.log('❌ @tanstack/react-query import failed:', error.message);
}

console.log('Module test complete.');
