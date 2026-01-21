import React, { useState, useEffect, useCallback } from 'react';
import type { WaferMapSpec, SamplingOutput } from '../../api/catalog';
import { generateWaferGrid } from './waferMap.utils';
import type { WaferMapModel } from './waferMap.utils';
import WaferMapCell from './WaferMapCell';
import { WaferMapLegend } from './WaferMapLegend';
import { Settings2 } from 'lucide-react';
import { Button } from '../../ui/Button';

interface WaferMapProps {
  waferMapSpec: WaferMapSpec;
  samplingOutput?: SamplingOutput | null;
  className?: string;
}

export const WaferMap: React.FC<WaferMapProps> = ({ 
  waferMapSpec, 
  samplingOutput,
  className = ""
}) => {
  const [model, setModel] = useState<WaferMapModel | null>(null);
  const [showValues, setShowValues] = useState(false);
  const [showCoords, setShowCoords] = useState(true);

  // Initialize model from props
  useEffect(() => {
    // Generate heavy grid only when inputs change
    const initialModel = generateWaferGrid(waferMapSpec, samplingOutput);
    setModel(initialModel);
  }, [waferMapSpec, samplingOutput]);

  // Handler for cell click - updates local state efficiently
  const handleCellToggle = useCallback((x: number, y: number) => {
    setModel(prev => {
      if (!prev) return null;
      
      // Find index in linear array. 
      // Helper: index = (yMax - y) * width + (x - xMin)
      // But we stored colIndex/rowIndex in cell, let's use that if we had a map.
      // Since we just have a list, we can map over it. 
      // Optimization: For 3600 items, map is O(N). Acceptable for click.
      // Better: Use calculated index.
      
      const { xRange, yRange, width } = prev;
      const xMin = xRange[0];
      const yMax = yRange[1];
      
      // Calculated index based on generation logic
      // r = yMax - y
      // c = x - xMin
      // index = r * width + c
      const r = yMax - y;
      const c = x - xMin;
      const idx = r * width + c;
      
      if (idx < 0 || idx >= prev.cells.length) return prev;

      // Shallow copy array
      const newCells = [...prev.cells];
      // Clone cell and toggle
      const target = newCells[idx];
      // Double check we hit the right cell
      if (target.x !== x || target.y !== y) {
        // Fallback to find if logic assumption wrong
        console.warn("Index mismatch in WaferMap toggle, falling back to find");
        const foundIdx = newCells.findIndex(c => c.x === x && c.y === y);
        if (foundIdx === -1) return prev;
        newCells[foundIdx] = { ...newCells[foundIdx], selected: !newCells[foundIdx].selected };
      } else {
        newCells[idx] = { ...target, selected: !target.selected };
      }

      return { ...prev, cells: newCells };
    });
  }, []);

  if (!model) return <div className="animate-pulse bg-slate-100 w-full h-96 rounded-lg"></div>;

  // Grid style
  const gridStyle = {
    display: 'grid',
    gridTemplateColumns: `repeat(${model.width}, minmax(0, 1fr))`,
    // Force square aspect ratio for cells if we want perfect squares
    // But usually fitting to container is easier. 
    // We'll trust the parent container's aspect ratio or just let it fill.
  };

  // Axes Generators
  const renderXAxis = () => {
    if (!showCoords) return null;
    const ticks = [];
    // Show tick every 5
    const [min, max] = model.xRange;
    for (let i = min; i <= max; i++) {
      if (i % 5 === 0) {
        // Calculate percentage position
        const pct = ((i - min) / (model.width - 1)) * 100;
        ticks.push(
          <div key={i} className="absolute text-[9px] text-slate-400 transform -translate-x-1/2" style={{ left: `${pct}%` }}>
            {i}
          </div>
        );
      }
    }
    return <div className="relative h-4 mt-1 w-full">{ticks}</div>;
  };

  const renderYAxis = () => {
    if (!showCoords) return null;
    const ticks = [];
    const [min, max] = model.yRange;
    for (let i = min; i <= max; i++) {
      if (i % 5 === 0) {
        // Y goes from max (top) to min (bottom)
        // pct 0 is top
        const pct = ((max - i) / (model.height - 1)) * 100;
        ticks.push(
          <div key={i} className="absolute text-[9px] text-slate-400 transform -translate-y-1/2 right-1" style={{ top: `${pct}%` }}>
            {i}
          </div>
        );
      }
    }
    return <div className="relative w-6 mr-1 h-full">{ticks}</div>;
  };

  return (
    <div className={`flex flex-col ${className}`}>
      {/* Controls */}
      <div className="flex justify-between items-center mb-2 px-1">
        <h3 className="text-sm font-semibold text-slate-700">Die Grid</h3>
        <div className="flex gap-2">
          <Button 
            variant="ghost" 
            size="sm" 
            className={`h-6 text-xs ${showValues ? 'bg-slate-100' : ''}`}
            onClick={() => setShowValues(!showValues)}
          >
            <Settings2 className="w-3 h-3 mr-1" />
            Values
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            className={`h-6 text-xs ${showCoords ? 'bg-slate-100' : ''}`}
            onClick={() => setShowCoords(!showCoords)}
          >
            Axes
          </Button>
        </div>
      </div>

      {/* Main Grid Layout with Axes */}
      <div className="flex flex-1 min-h-0 bg-white border rounded-lg p-4 shadow-sm">
        {/* Y Axis Col */}
        <div className="flex flex-col">
           <div className="flex-1 relative">
             {renderYAxis()}
           </div>
           {/* Spacer for X axis height */}
           {showCoords && <div className="h-4"></div>}
        </div>

        {/* Grid Content Col */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex-1 relative aspect-square"> 
             {/* Aspect square ensures wafers look round-ish not stretched */}
             <div className="absolute inset-0" style={gridStyle}>
               {model.cells.map((cell) => (
                 <WaferMapCell 
                   key={`${cell.x},${cell.y}`} 
                   cell={cell} 
                   showValue={showValues}
                   onToggle={handleCellToggle}
                 />
               ))}
             </div>
          </div>
          {/* X Axis */}
          {renderXAxis()}
        </div>
      </div>

      <WaferMapLegend />
    </div>
  );
};
