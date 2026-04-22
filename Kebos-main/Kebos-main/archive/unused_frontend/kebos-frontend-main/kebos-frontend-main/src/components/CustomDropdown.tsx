import React, { useState, useRef, useEffect } from "react";

interface Option {
  value: string;
  label: string;
}

interface CustomDropdownProps {
  value: string;
  options: Option[];
  onChange: (value: string) => void;
  label?: string;
  className?: string;
  placeholder?: string;
}

export const CustomDropdown: React.FC<CustomDropdownProps> = ({
  value,
  options,
  onChange,
  label,
  className = "",
  placeholder = "Select...",
}) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selected = options.find((opt) => opt.value === value);

  return (
    <div className={`relative ${className}`} ref={ref}>
      {label && (
        <label className="block text-sm font-semibold text-slate-700 mb-3">
          {label}
        </label>
      )}
      <button
        type="button"
        className={`w-full bg-white rounded-xl border border-slate-200 px-5 py-3.5 text-slate-700 font-medium shadow-sm flex justify-between items-center
          hover:border-slate-300 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/20
          transition-all duration-200 ease-out transform hover:scale-[1.02] active:scale-[0.98]`}
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span>
          {selected ? (
            selected.label
          ) : (
            <span className="text-slate-400">{placeholder}</span>
          )}
        </span>
        <svg
          className={`h-5 w-5 ml-2 transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      {open && (
        <ul
          className="absolute left-0 z-20 mt-2 w-full bg-white rounded-xl shadow-xl border border-slate-200 py-2 transition-all duration-200 animate-fade-in
            origin-top transform"
          style={{ minWidth: "100%", top: "100%" }}
          role="listbox"
        >
          {options.map((opt) => (
            <li
              key={opt.value}
              className={`px-5 py-3.5 cursor-pointer text-slate-700 hover:bg-indigo-50 hover:text-indigo-700 transition-colors duration-150 ${
                value === opt.value
                  ? "bg-indigo-100 text-indigo-700 font-semibold"
                  : ""
              }`}
              onClick={() => {
                onChange(opt.value);
                setOpen(false);
              }}
              role="option"
              aria-selected={value === opt.value}
            >
              {opt.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default CustomDropdown;
