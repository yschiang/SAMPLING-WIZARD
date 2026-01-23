import type { WaferMapSpec, SamplingOutput } from '../../api/catalog';

export type Cell = {
  // Grid indices (for rendering order if needed, though we just map linear)
  colIndex: number;
  rowIndex: number;
  
  // Die coordinates (logical)
  x: number;
  y: number;
  
  value?: number;     // 0..100
  valid: boolean;     // mask
  selected?: boolean; // UI state
};

export type WaferMapModel = {
  width: number;
  height: number;
  cells: Cell[];
  xRange: [number, number]; // [min, max]
  yRange: [number, number]; // [min, max]
};

// Color levels mapping (Tailwind classes)
export const LEVEL_CLASSES = {
  INVALID: 'bg-neutral-100 border-transparent', // muted
  VALID_EMPTY: 'bg-white border-neutral-200 hover:border-neutral-400', // neutral
  LEVEL_1: 'bg-blue-50 border-blue-200',
  LEVEL_2: 'bg-blue-100 border-blue-300',
  LEVEL_3: 'bg-blue-300 border-blue-400',
  LEVEL_4: 'bg-blue-500 border-blue-600',
  LEVEL_5: 'bg-blue-700 border-blue-800',
  SELECTED: 'ring-2 ring-indigo-600 z-10', // overlay
};

export const getCellColorClass = (cell: Cell): string => {
  if (!cell.valid) return LEVEL_CLASSES.INVALID;
  if (cell.value === undefined) return LEVEL_CLASSES.VALID_EMPTY;
  
  const v = cell.value;
  if (v < 20) return LEVEL_CLASSES.LEVEL_1;
  if (v < 40) return LEVEL_CLASSES.LEVEL_2;
  if (v < 60) return LEVEL_CLASSES.LEVEL_3;
  if (v < 80) return LEVEL_CLASSES.LEVEL_4;
  return LEVEL_CLASSES.LEVEL_5;
};

export const generateWaferGrid = (
  spec: WaferMapSpec, 
  samplingOutput?: SamplingOutput | null
): WaferMapModel => {
  const { wafer_size_mm, die_pitch_x_mm, die_pitch_y_mm, valid_die_mask } = spec;
  const radius = wafer_size_mm / 2;
  
  // 1. Calculate Grid Bounds (Die Coordinates)
  // Assuming Origin CENTER (0,0) is center of wafer
  // Max die index approx radius / pitch
  const xMax = Math.floor(radius / die_pitch_x_mm);
  const yMax = Math.floor(radius / die_pitch_y_mm);
  
  const xMin = -xMax;
  const yMin = -yMax;
  
  const width = xMax - xMin + 1;
  const height = yMax - yMin + 1;
  
  // 2. Prepare Selection Set for O(1) lookup
  const selectedSet = new Set<string>();
  if (samplingOutput?.selected_points) {
    samplingOutput.selected_points.forEach(p => {
      selectedSet.add(`${p.die_x},${p.die_y}`);
    });
  }

  // 3. Generate Cells
  const cells: Cell[] = [];
  
  // Render order: Top-Left to Bottom-Right
  // Logical Y goes UP, Grid Row goes DOWN.
  // Row 0 -> Y = yMax
  // Row H-1 -> Y = yMin
  
  for (let r = 0; r < height; r++) {
    const dieY = yMax - r;
    
    for (let c = 0; c < width; c++) {
      const dieX = xMin + c;
      
      // Validity Check (Geometric mask)
      // Center of die (approx) distance to center (0,0)
      // distance = sqrt((x*pitch)^2 + (y*pitch)^2)
      const distX = dieX * die_pitch_x_mm;
      const distY = dieY * die_pitch_y_mm;
      const distance = Math.sqrt(distX*distX + distY*distY);
      
      // Simple validity check based on Edge Exclusion
      // If mask type is explicit list, we'd check that instead.
      // Default to radius check.
      const validRadius = valid_die_mask.radius_mm || (radius - 3); // default 3mm edge exclusion
      const isValid = distance <= validRadius;
      
      const isSelected = selectedSet.has(`${dieX},${dieY}`);
      
      let value: number | undefined = undefined;
      
      cells.push({
        colIndex: c,
        rowIndex: r,
        x: dieX,
        y: dieY,
        valid: isValid,
        selected: isSelected,
        value
      });
    }
  }
  
  return {
    width,
    height,
    cells,
    xRange: [xMin, xMax],
    yRange: [yMin, yMax]
  };
};
