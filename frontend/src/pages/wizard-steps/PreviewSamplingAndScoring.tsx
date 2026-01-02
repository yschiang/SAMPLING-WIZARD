import { useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { WizardContext } from '../../context/WizardContext';
import WaferMapViewer from '../../components/WaferMapViewer';
import { generateRecipe } from '../../api/catalog';

const PreviewSamplingAndScoring = () => {
  const { state, dispatch } = useContext(WizardContext);
  const navigate = useNavigate();

  const { waferMapSpec, toolProfile } = state.derived;
  const { samplingOutput, previewWarnings, scoreReport } = state.outputs;

  const handleGenerateRecipe = async () => {
    if (!waferMapSpec || !toolProfile || !samplingOutput) {
      dispatch({
        type: 'SET_ERROR',
        payload: 'Cannot generate recipe. Missing one or more required inputs.',
      });
      return;
    }

    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      const requestBody = {
        wafer_map_spec: waferMapSpec,
        tool_profile: toolProfile,
        sampling_output: samplingOutput,
        ...(scoreReport && { score_report: scoreReport }),
      };
      const response = await generateRecipe(requestBody);
      dispatch({ type: 'SET_RECIPE_OUTPUT', payload: response.tool_recipe });
      navigate('/wizard/generate-and-review-recipe');
    } catch (err: any) {
      dispatch({ type: 'SET_ERROR', payload: err.message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  if (state.isLoading && !samplingOutput) {
    return <p>Loading preview and scores...</p>;
  }

  if (!samplingOutput) {
    return (
      <div>
        <h3>Step 5: Preview Sampling & Scoring</h3>
        <p>No preview data available. Please select a strategy and click "Preview & Score" in the previous step.</p>
        {state.error && <p style={{ color: 'red' }}>Error: {state.error}</p>}
      </div>
    );
  }

  return (
    <div>
      <h3>Step 5: Preview Sampling & Scoring</h3>
      <div style={{ display: 'flex', gap: '20px' }}>
        <div style={{ flex: 1 }}>
          <h4>Wafer Map</h4>
          <WaferMapViewer waferMapSpec={waferMapSpec} samplingOutput={samplingOutput} />
        </div>
        <div style={{ flex: 2 }}>
          <div style={{ display: 'flex', gap: '20px' }}>
            <div style={{ flex: 1 }}>
              <h4>Selected Points ({samplingOutput.selected_points.length})</h4>
              <div style={{ height: '300px', overflowY: 'auto', border: '1px solid #ccc' }}>
                <table>
                  <thead>
                    <tr>
                      <th>Die X</th>
                      <th>Die Y</th>
                    </tr>
                  </thead>
                  <tbody>
                    {samplingOutput.selected_points.map((point, i) => (
                      <tr key={i}>
                        <td>{point.die_x}</td>
                        <td>{point.die_y}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div style={{ flex: 1 }}>
              <h4>Score Panel</h4>
              {state.isLoading && !scoreReport && <p>Loading scores...</p>}
              {scoreReport ? (
                <div>
                  <p><strong>Overall Score: {scoreReport.overall_score.toFixed(2)}</strong></p>
                  <ul>
                    <li>Coverage: {scoreReport.coverage_score.toFixed(2)}</li>
                    <li>Statistical: {scoreReport.statistical_score.toFixed(2)}</li>
                    <li>Risk Alignment: {scoreReport.risk_alignment_score.toFixed(2)}</li>
                  </ul>
                  <h5>Score Warnings:</h5>
                  {scoreReport.warnings.length > 0 ? (
                    <ul>
                      {scoreReport.warnings.map((warning, i) => (
                        <li key={i} style={{ color: 'orange' }}>
                          <strong>{warning.code}:</strong> {warning.message}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p>No score warnings.</p>
                  )}
                </div>
              ) : (
                !state.isLoading && <p>Score report not available.</p>
              )}
            </div>
          </div>
          <div style={{ marginTop: '20px' }}>
            <h4>Preview Warnings</h4>
            {previewWarnings.length > 0 ? (
              <ul>
                {previewWarnings.map((warning, i) => (
                  <li key={i} style={{ color: 'orange' }}>
                    <strong>{warning.code}:</strong> {warning.message}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No preview warnings.</p>
            )}
          </div>
          <div style={{ marginTop: '20px' }}>
            <button
              onClick={handleGenerateRecipe}
              disabled={state.isLoading || !samplingOutput}
            >
              Generate Recipe
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PreviewSamplingAndScoring;
