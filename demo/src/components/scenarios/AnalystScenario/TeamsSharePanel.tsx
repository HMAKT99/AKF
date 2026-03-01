import { useState, useEffect } from "react";
import SystemBadge from "../../shared/SystemBadge";

interface TeamsSharePanelProps {
  docTitle: string;
  onComplete: () => void;
}

export default function TeamsSharePanel({ docTitle, onComplete }: TeamsSharePanelProps) {
  const [showDelivery, setShowDelivery] = useState(false);
  const [showReply, setShowReply] = useState(false);

  // Show delivery confirmation after 1s
  useEffect(() => {
    const timer = setTimeout(() => setShowDelivery(true), 1000);
    return () => clearTimeout(timer);
  }, []);

  // Show reply after delivery + 1s
  useEffect(() => {
    if (!showDelivery) return;
    const timer = setTimeout(() => setShowReply(true), 1000);
    return () => clearTimeout(timer);
  }, [showDelivery]);

  // Call onComplete after reply
  useEffect(() => {
    if (!showReply) return;
    const timer = setTimeout(() => onComplete(), 1500);
    return () => clearTimeout(timer);
  }, [showReply, onComplete]);

  return (
    <div className="animate-fade-in rounded-xl overflow-hidden border border-gray-200 shadow-lg bg-white">
      {/* Teams title bar */}
      <div className="flex items-center gap-2 px-4 py-2 bg-[#6264A7]">
        {/* Teams icon */}
        <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19.19 8.77a2.27 2.27 0 1 0 0-4.54 2.27 2.27 0 0 0 0 4.54zM22 10.5h-4.36c.33.54.53 1.17.53 1.84v5.52a.73.73 0 0 1 0 .14H22a1 1 0 0 0 1-1V12a1.5 1.5 0 0 0-1-1.5z" />
          <path d="M14.5 7.25a3.25 3.25 0 1 0-6.5 0 3.25 3.25 0 0 0 6.5 0zM17.17 10H5.83A1.83 1.83 0 0 0 4 11.83v6.34A1.83 1.83 0 0 0 5.83 20h11.34A1.83 1.83 0 0 0 19 18.17v-6.34A1.83 1.83 0 0 0 17.17 10z" />
        </svg>
        <span className="text-white text-sm font-medium flex-1">Microsoft Teams</span>
        <SystemBadge system="teams" />
      </div>

      <div className="flex" style={{ minHeight: 380 }}>
        {/* Left sidebar - channels */}
        <div className="w-52 bg-[#292b4a] text-gray-300 text-xs shrink-0">
          <div className="px-3 py-2.5 text-[10px] uppercase tracking-wider text-gray-500 font-semibold">
            Channels
          </div>
          <div className="px-3 py-1.5 text-gray-400 hover:bg-white/5 cursor-default">
            # General
          </div>
          <div className="px-3 py-1.5 bg-white/10 text-white font-medium rounded-r-sm border-l-2 border-purple-400">
            # Q3 Analysis Review
          </div>
          <div className="px-3 py-1.5 text-gray-400 hover:bg-white/5 cursor-default">
            # Finance
          </div>
          <div className="px-3 py-1.5 text-gray-400 hover:bg-white/5 cursor-default">
            # Leadership
          </div>
        </div>

        {/* Right: Chat area */}
        <div className="flex-1 flex flex-col">
          {/* Channel header */}
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-gray-800">Q3 Analysis Review</span>
              <span className="text-[10px] text-gray-400 bg-gray-200 px-1.5 py-0.5 rounded-full">
                3 participants
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              {/* Participant avatars */}
              <div className="flex -space-x-1.5">
                <div className="w-6 h-6 rounded-full bg-blue-500 border-2 border-white flex items-center justify-center text-white text-[9px] font-bold">
                  S
                </div>
                <div className="w-6 h-6 rounded-full bg-green-500 border-2 border-white flex items-center justify-center text-white text-[9px] font-bold">
                  M
                </div>
                <div className="w-6 h-6 rounded-full bg-orange-500 border-2 border-white flex items-center justify-center text-white text-[9px] font-bold">
                  J
                </div>
              </div>
            </div>
          </div>

          {/* Messages area */}
          <div className="flex-1 overflow-auto p-4 space-y-4 bg-white">
            {/* Sarah's message */}
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white text-xs font-bold shrink-0">
                S
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-semibold text-gray-800">Sarah Chen</span>
                  <span className="text-[10px] text-gray-400">sarah@woodgrove.com</span>
                  <span className="text-[10px] text-gray-400">Just now</span>
                </div>
                <p className="text-sm text-gray-700 mb-2">
                  Here's the Q3 analysis with Copilot-generated summary. Please review the revenue claims.
                </p>

                {/* File attachment card */}
                <div className="border border-gray-200 rounded-lg overflow-hidden max-w-sm shadow-sm">
                  <div className="flex items-center gap-3 px-3 py-2.5 bg-gray-50">
                    {/* Excel icon */}
                    <div className="w-10 h-10 bg-[#217346] rounded-lg flex items-center justify-center shrink-0">
                      <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z" />
                        <path d="M8.5 13.5l1.7 2.5-1.7 2.5h1.5l1-1.6 1 1.6h1.5l-1.7-2.5 1.7-2.5H12l-1 1.6-1-1.6H8.5z" opacity="0.6" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 truncate">{docTitle}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] text-gray-500 bg-gray-200 px-1.5 py-0.5 rounded font-medium">
                          4 claims
                        </span>
                        <span className="text-[10px] text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded font-medium">
                          confidential
                        </span>
                      </div>
                    </div>
                  </div>
                  {/* Trust indicator bar */}
                  <div className="flex items-center gap-1.5 px-3 py-1.5 bg-green-50 border-t border-green-200">
                    <svg className="w-3.5 h-3.5 text-green-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    <span className="text-[11px] font-medium text-green-700">
                      All claims verified
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Delivery confirmation */}
            {showDelivery && (
              <div className="flex items-center justify-center gap-2 animate-slide-in">
                <div className="h-px flex-1 bg-gray-200" />
                <div className="flex items-center gap-1.5 text-[11px] text-green-600 bg-green-50 px-3 py-1 rounded-full">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span className="font-medium">Shared internally — AKF metadata preserved</span>
                </div>
                <div className="h-px flex-1 bg-gray-200" />
              </div>
            )}

            {/* Reviewer reply */}
            {showReply && (
              <div className="flex items-start gap-3 animate-slide-in">
                <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center text-white text-xs font-bold shrink-0">
                  M
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-semibold text-gray-800">Michael Torres</span>
                    <span className="text-[10px] text-gray-400">michael@woodgrove.com</span>
                    <span className="text-[10px] text-gray-400">Just now</span>
                  </div>
                  <p className="text-sm text-gray-700">
                    Looks good, I've verified the revenue claim against the 10-Q.
                    <span className="inline-flex items-center gap-0.5 text-green-600 ml-1">
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </span>
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Compose bar */}
          <div className="border-t border-gray-200 px-4 py-2.5 bg-gray-50">
            <div className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-3 py-2">
              <span className="text-sm text-gray-400 flex-1">Type a message...</span>
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
