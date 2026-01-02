import { useContext } from 'react';
import { WizardContext } from '../../context/WizardContext';

const GenerateAndReviewRecipe = () => {
  const { state } = useContext(WizardContext);
  const { toolRecipe, previewWarnings } = state.outputs; // Also display previewWarnings here per spec

  const handleExportRecipe = () => {
    if (toolRecipe && toolRecipe.recipe_payload) {
      const json = JSON.stringify(toolRecipe.recipe_payload, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const href = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = href;
      link.download = `sampling-recipe-${toolRecipe.recipe_id}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(href);
    }
  };

  if (state.isLoading && !toolRecipe) {
    return <p>Generating recipe...</p>;
  }

  if (!toolRecipe) {
    return (
      <div>
        <h3>Step 6: Generate & Review Recipe</h3>
        <p>No recipe generated. Please complete previous steps and click "Generate Recipe" in the previous step.</p>
        {state.error && <p style={{ color: 'red' }}>Error: {state.error}</p>}
      </div>
    );
  }

  return (
    <div>
      <h3>Step 6: Generate & Review Recipe</h3>
      {state.error && <p style={{ color: 'red' }}>Error: {state.error}</p>}

      <h4>Tool Recipe ({toolRecipe.recipe_id})</h4>
      <p>Tool Type: {toolRecipe.tool_type}</p>
      <p>Recipe Format Version: {toolRecipe.recipe_format_version}</p>

      <h5>Recipe Payload:</h5>
      <pre style={{ backgroundColor: '#eee', padding: '10px', borderRadius: '5px', overflowX: 'auto' }}>
        <code>{JSON.stringify(toolRecipe.recipe_payload, null, 2)}</code>
      </pre>

      {toolRecipe.translation_notes && toolRecipe.translation_notes.length > 0 && (
        <div>
          <h5>Translation Notes:</h5>
          <ul>
            {toolRecipe.translation_notes.map((note, i) => (
              <li key={i}>{note}</li>
            ))}
          </ul>
        </div>
      )}

      {previewWarnings.length > 0 && (
        <div style={{ marginTop: '20px' }}>
          <h4>Warnings from Preview:</h4>
          <ul>
            {previewWarnings.map((warning, i) => (
              <li key={i} style={{ color: 'orange' }}>
                <strong>{warning.code}:</strong> {warning.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ marginTop: '20px' }}>
        <button onClick={handleExportRecipe}>Export Recipe JSON</button>
      </div>
    </div>
  );
};

export default GenerateAndReviewRecipe;
