
export function Footer() {
  return (
    <footer className="h-12 bg-secondary-dark border-t border-quaternary px-4 flex items-center justify-between text-sm text-gray-400">
      <div className="flex items-center space-x-4">
        <span>© 2025 Cyber Threat Platform</span>
        <span>•</span>
        <span>Version 1.0.0</span>
      </div>
      
      <div className="flex items-center space-x-4">
        <span>Status: Online</span>
        <div className="w-2 h-2 bg-success rounded-full"></div>
      </div>
    </footer>
  );
}
