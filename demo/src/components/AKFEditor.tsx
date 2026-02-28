import { useState } from 'react';
import type { Claim, AKFUnit } from '../lib/akf';
import { createUnit } from '../lib/akf';
import ClaimCard from './ClaimCard';
import AKFCodeView from './AKFCodeView';

interface AKFEditorProps {
  onComplete: (unit: AKFUnit) => void;
}

const TIERS = [1, 2, 3, 4, 5];
const CLASSIFICATIONS = ['public', 'internal', 'confidential', 'highly-confidential', 'restricted'];

export default function AKFEditor({ onComplete }: AKFEditorProps) {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [content, setContent] = useState('');
  const [trust, setTrust] = useState(0.8);
  const [source, setSource] = useState('');
  const [tier, setTier] = useState(2);
  const [verified, setVerified] = useState(false);
  const [author, setAuthor] = useState('sarah@woodgrove.com');
  const [classification, setClassification] = useState('confidential');
  const [unit, setUnit] = useState<AKFUnit | null>(null);

  const addClaim = () => {
    if (!content.trim()) return;
    const claim: Claim = {
      c: content.trim(),
      t: trust,
      src: source || undefined,
      tier,
      verified: verified || undefined,
    };
    setClaims(prev => [...prev, claim]);
    setContent('');
    setSource('');
    setTrust(0.8);
    setVerified(false);
  };

  const createAkf = () => {
    if (claims.length === 0) return;
    const u = createUnit(claims, { author, classification });
    setUnit(u);
    onComplete(u);
  };

  // Generate a live preview unit for the JSON view
  const previewUnit: AKFUnit | null =
    unit ?? (claims.length > 0
      ? {
          "$akf": "1.0",
          id: "(preview)",
          ts: new Date().toISOString(),
          author,
          classification,
          claims,
          prov: [{ by: author, action: 'created', ts: new Date().toISOString(), delta: `+${claims.length} claims` }],
        }
      : null);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Left: Form + Claims */}
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800 mb-1">Hop 1: Human Creates</h2>
          <p className="text-sm text-gray-500">
            Author creates claims with trust scores and provenance metadata.
          </p>
        </div>

        {/* Author & Classification */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Author</label>
            <input
              type="text"
              value={author}
              onChange={e => setAuthor(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Classification</label>
            <select
              value={classification}
              onChange={e => setClassification(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white"
            >
              {CLASSIFICATIONS.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Claim Form */}
        <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-600 mb-1">Claim Content</label>
            <textarea
              value={content}
              onChange={e => setContent(e.target.value)}
              rows={2}
              placeholder="Enter a factual claim..."
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">
                Trust: {trust.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={trust}
                onChange={e => setTrust(parseFloat(e.target.value))}
                className="w-full accent-blue-600"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Source</label>
              <input
                type="text"
                value={source}
                onChange={e => setSource(e.target.value)}
                placeholder="e.g. 10-K filing"
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-600 mb-1">Tier</label>
              <select
                value={tier}
                onChange={e => setTier(parseInt(e.target.value))}
                className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white"
              >
                {TIERS.map(t => (
                  <option key={t} value={t}>Tier {t}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
              <input
                type="checkbox"
                checked={verified}
                onChange={e => setVerified(e.target.checked)}
                className="w-4 h-4 accent-blue-600"
              />
              Verified
            </label>
            <button
              onClick={addClaim}
              disabled={!content.trim()}
              className="ml-auto px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-md hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              + Add Claim
            </button>
          </div>
        </div>

        {/* Claims list */}
        {claims.length > 0 && (
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-gray-600">Claims ({claims.length})</h3>
            {claims.map((claim, i) => (
              <ClaimCard key={i} claim={claim} index={i} />
            ))}
          </div>
        )}

        {/* Create button */}
        {claims.length > 0 && !unit && (
          <button
            onClick={createAkf}
            className="w-full py-3 bg-blue-600 text-white font-bold rounded-lg hover:bg-blue-700 transition-colors shadow-md"
          >
            Create .akf Unit
          </button>
        )}

        {unit && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
            <span className="text-green-700 font-semibold">
              AKF unit created successfully. Proceed to Step 2.
            </span>
          </div>
        )}
      </div>

      {/* Right: JSON Preview */}
      <div className="space-y-4">
        <h3 className="text-sm font-semibold text-gray-600">Live JSON Preview</h3>
        <AKFCodeView unit={previewUnit} />
      </div>
    </div>
  );
}
