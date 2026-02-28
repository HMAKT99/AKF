import type { AKFUnit } from '../lib/akf';

interface AKFCodeViewProps {
  unit: AKFUnit | null;
}

function syntaxHighlight(json: string): string {
  return json.replace(
    /("(\\u[a-fA-F0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
    (match) => {
      let cls = 'text-emerald-600'; // number
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'text-blue-600 font-semibold'; // key
        } else {
          cls = 'text-amber-700'; // string
        }
      } else if (/true|false/.test(match)) {
        cls = 'text-purple-600'; // boolean
      } else if (/null/.test(match)) {
        cls = 'text-gray-400'; // null
      }
      return `<span class="${cls}">${match}</span>`;
    }
  );
}

export default function AKFCodeView({ unit }: AKFCodeViewProps) {
  if (!unit) {
    return (
      <div className="bg-gray-50 border border-dashed border-gray-300 rounded-lg p-6 text-center text-gray-400 text-sm">
        Create claims to see the .akf JSON preview
      </div>
    );
  }

  const json = JSON.stringify(unit, null, 2);
  const highlighted = syntaxHighlight(json);

  return (
    <div className="bg-gray-900 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-red-500" />
          <span className="w-3 h-3 rounded-full bg-amber-500" />
          <span className="w-3 h-3 rounded-full bg-green-500" />
        </div>
        <span className="text-xs text-gray-400 font-mono">.akf</span>
      </div>
      <pre
        className="p-4 text-xs leading-relaxed overflow-auto max-h-[500px] bg-gray-900 text-gray-300"
        dangerouslySetInnerHTML={{ __html: highlighted }}
      />
    </div>
  );
}
