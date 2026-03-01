import type { AKFUnit } from '../../lib/akf';
import AKFCodeView from './AKFCodeView';
import ProvenanceTree from './ProvenanceTree';

interface AKFPeekPanelProps {
  unit: AKFUnit | null;
  open: boolean;
  onClose: () => void;
  filename?: string;
}

export default function AKFPeekPanel({ unit, open, onClose, filename }: AKFPeekPanelProps) {
  return (
    <>
      {/* Backdrop overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/30 z-50 transition-opacity duration-300"
          onClick={onClose}
        />
      )}

      {/* Slide-out drawer */}
      <div
        className={`fixed top-0 right-0 h-full w-[400px] bg-white shadow-2xl z-50 flex flex-col transition-transform duration-300 ease-in-out ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-gray-50 shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
              .akf
            </span>
            <span className="text-sm font-semibold text-gray-700 truncate">
              {filename || 'unit.akf'}
            </span>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-gray-200 transition-colors text-gray-500 hover:text-gray-800"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          <AKFCodeView unit={unit} filename={filename} />

          {unit?.prov && unit.prov.length > 0 && (
            <ProvenanceTree hops={unit.prov} />
          )}
        </div>
      </div>
    </>
  );
}
