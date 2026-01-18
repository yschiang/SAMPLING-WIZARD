import { useMemo } from 'react';

interface StrategyPreviewProps {
  strategyId: string;
  size?: number;
}

export const StrategyPreview = ({ strategyId, size = 120 }: StrategyPreviewProps) => {
  const points = useMemo(() => {
    const pts: { x: number; y: number }[] = [];
    const radius = 45; // slightly less than 50 (half of 100 viewbox) to stay in circle
    
    // Normalize strategy ID for logic mapping
    const type = strategyId.toUpperCase();

    if (type.includes('GRID')) {
      // UNIFORM_GRID
      const step = 15;
      for (let x = -radius; x <= radius; x += step) {
        for (let y = -radius; y <= radius; y += step) {
          if (x*x + y*y <= radius*radius) {
            pts.push({ x, y });
          }
        }
      }
    } else if (type.includes('EDGE_ONLY')) {
      // EDGE_RING
      const count = 20;
      for (let i = 0; i < count; i++) {
        const angle = (i / count) * 2 * Math.PI;
        pts.push({
          x: Math.cos(angle) * (radius - 2),
          y: Math.sin(angle) * (radius - 2)
        });
      }
    } else if (type.includes('ZONE') || type.includes('RING')) {
      // MULTI_RING_ZONES
      const rings = 3;
      const pointsPerRing = 8;
      for (let r = 1; r <= rings; r++) {
        const currentRadius = (radius / rings) * r;
        for (let i = 0; i < pointsPerRing; i++) {
          const angle = (i / pointsPerRing) * 2 * Math.PI + (r % 2 ? 0 : Math.PI/pointsPerRing);
          pts.push({
            x: Math.cos(angle) * currentRadius,
            y: Math.sin(angle) * currentRadius
          });
        }
      }
    } else {
      // Default: CENTER_EDGE / RING_CENTER_BIASED
      // Center point
      pts.push({ x: 0, y: 0 });
      // Inner ring
      const innerCount = 6;
      for (let i = 0; i < innerCount; i++) {
        const angle = (i / innerCount) * 2 * Math.PI;
        pts.push({ x: Math.cos(angle) * 15, y: Math.sin(angle) * 15 });
      }
      // Outer ring
      const outerCount = 12;
      for (let i = 0; i < outerCount; i++) {
        const angle = (i / outerCount) * 2 * Math.PI + 0.2; // slight offset
        pts.push({ x: Math.cos(angle) * 40, y: Math.sin(angle) * 40 });
      }
    }
    
    return pts;
  }, [strategyId]);

  return (
    <div className="relative flex flex-col items-center pointer-events-none">
      <svg 
        width={size} 
        height={size} 
        viewBox="-55 -55 110 110" 
        className="text-primary overflow-visible"
      >
        {/* Wafer Circle */}
        <circle 
          cx="0" 
          cy="0" 
          r="50" 
          fill="none" 
          stroke="currentColor" 
          strokeWidth="1.5" 
          className="text-muted-foreground/20"
        />
        
        {/* Notch/Flat indicator */}
        <path 
          d="M -5 50 L 5 50" 
          stroke="currentColor" 
          strokeWidth="2" 
          className="text-muted-foreground/40" 
        />

        {/* Points */}
        {points.map((p, i) => (
          <circle 
            key={i} 
            cx={p.x} 
            cy={p.y} 
            r="2" 
            className="fill-primary"
          />
        ))}
      </svg>
      <span className="text-[9px] text-muted-foreground/60 mt-3 font-medium uppercase tracking-wider">
        Preview (Illustration)
      </span>
    </div>
  );
};