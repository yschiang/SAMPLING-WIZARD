import React from 'react';
import { getCellColorClass } from './waferMap.utils';
import type { Cell } from './waferMap.utils';

interface WaferMapCellProps {
  cell: Cell;
  showValue: boolean;
  onToggle: (x: number, y: number) => void;
}

const WaferMapCell: React.FC<WaferMapCellProps> = ({ cell, showValue, onToggle }) => {
  const { x, y, value, valid, selected } = cell;
  
  const handleClick = () => {
    if (valid) {
      onToggle(x, y);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  };

  const colorClass = getCellColorClass(cell);
  const selectedClass = selected ? 'ring-2 ring-indigo-600 z-10' : '';
  const cursorClass = valid ? 'cursor-pointer' : 'cursor-not-allowed opacity-50';
  
  // Minimal content: Value if present and enabled
  const content = showValue && value !== undefined ? (
    <span className="text-[10px] leading-none font-semibold text-slate-700 pointer-events-none">
      {value}
    </span>
  ) : null;

  return (
    <div
      role="gridcell"
      aria-label={`x: ${x}, y: ${y}, value: ${value ?? 'N/A'}, ${valid ? 'valid' : 'invalid'}, ${selected ? 'selected' : 'unselected'}`}
      aria-selected={selected}
      tabIndex={valid ? 0 : -1}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      title={`(${x}, ${y})${value !== undefined ? ` Val: ${value}` : ''}`}
      className={`
        relative w-full h-full flex items-center justify-center
        border border-black/5
        transition-colors duration-75
        hover:border-black/30 hover:z-20
        ${colorClass}
        ${selectedClass}
        ${cursorClass}
      `}
    >
      {content}
      {selected && (
        <div className="absolute top-0 right-0 w-1.5 h-1.5 bg-indigo-600 rounded-bl-sm" />
      )}
    </div>
  );
};

// Memoize to prevent re-rendering all 3600 cells when parent state changes (unless props change)
export default React.memo(WaferMapCell, (prev, next) => {
  return (
    prev.showValue === next.showValue &&
    prev.cell === next.cell // Reliance on immutable cell updates in parent
  );
});
