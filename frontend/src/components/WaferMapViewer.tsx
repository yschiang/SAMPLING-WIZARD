import type { WaferMapSpec, SamplingOutput } from '../api/catalog';

interface WaferMapViewerProps {
  waferMapSpec: WaferMapSpec | null;
  samplingOutput: SamplingOutput | null;
}

const WaferMapViewer = ({ waferMapSpec, samplingOutput }: WaferMapViewerProps) => {
  if (!waferMapSpec) {
    return <p>No Wafer Map Spec available.</p>;
  }

  const { wafer_size_mm, die_pitch_x_mm, die_pitch_y_mm } = waferMapSpec;
  const points = samplingOutput?.selected_points || [];

  // Basic SVG dimensions and scaling
  const svgSize = 400;
  const padding = 20;
  const waferRadius = wafer_size_mm / 2;
  const scale = (svgSize - padding * 2) / (waferRadius * 2);

  // Find max die coordinates to help with centering
  const maxDieX = Math.max(...points.map((p) => Math.abs(p.die_x)), 0);
  const maxDieY = Math.max(...points.map((p) => Math.abs(p.die_y)), 0);
  const maxDim = Math.max(maxDieX * die_pitch_x_mm, maxDieY * die_pitch_y_mm) * 1.1;
  const renderScale = (svgSize - padding * 2) / (maxDim * 2);


  return (
    <svg width={svgSize} height={svgSize} style={{ border: '1px solid #ccc' }}>
      {/* Wafer Circle */}
      <circle
        cx={svgSize / 2}
        cy={svgSize / 2}
        r={waferRadius * scale}
        fill="#f0f0f0"
        stroke="#ddd"
      />

      {/* Center of the wafer */}
      <line x1={svgSize/2 - 5} y1={svgSize/2} x2={svgSize/2 + 5} y2={svgSize/2} stroke="red" />
      <line x1={svgSize/2} y1={svgSize/2 - 5} x2={svgSize/2} y2={svgSize/2 + 5} stroke="red" />


      {/* Selected Points */}
      {points.map((point, i) => {
        const svgX = svgSize / 2 + point.die_x * die_pitch_x_mm * renderScale;
        const svgY = svgSize / 2 - point.die_y * die_pitch_y_mm * renderScale; // Y is inverted in SVG
        return (
          <circle
            key={i}
            cx={svgX}
            cy={svgY}
            r={3}
            fill="blue"
            opacity="0.7"
          >
            <title>({point.die_x}, {point.die_y})</title>
          </circle>
        );
      })}
    </svg>
  );
};

export default WaferMapViewer;
