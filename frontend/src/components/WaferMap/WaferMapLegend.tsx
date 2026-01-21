import { LEVEL_CLASSES } from './waferMap.utils';

export const WaferMapLegend = () => {
  return (
    <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 mt-2 p-2 bg-slate-50 rounded-md border border-slate-100">
      <span className="font-medium mr-1">Legend:</span>
      
      <div className="flex items-center gap-1.5">
        <div className={`w-3 h-3 border ${LEVEL_CLASSES.INVALID}`}></div>
        <span>Invalid</span>
      </div>
      
      <div className="flex items-center gap-1.5">
        <div className={`w-3 h-3 border ${LEVEL_CLASSES.VALID_EMPTY}`}></div>
        <span>Valid</span>
      </div>

      <div className="flex items-center gap-1">
        <div className={`w-3 h-3 border ${LEVEL_CLASSES.LEVEL_1}`}></div>
        <div className={`w-3 h-3 border ${LEVEL_CLASSES.LEVEL_2}`}></div>
        <div className={`w-3 h-3 border ${LEVEL_CLASSES.LEVEL_3}`}></div>
        <div className={`w-3 h-3 border ${LEVEL_CLASSES.LEVEL_4}`}></div>
        <div className={`w-3 h-3 border ${LEVEL_CLASSES.LEVEL_5}`}></div>
        <span>Value (Low → High)</span>
      </div>

      <div className="flex items-center gap-1.5 ml-2">
        <div className={`w-3 h-3 border border-indigo-600 bg-white ring-1 ring-indigo-600`}></div>
        <span>Selected</span>
      </div>
    </div>
  );
};
