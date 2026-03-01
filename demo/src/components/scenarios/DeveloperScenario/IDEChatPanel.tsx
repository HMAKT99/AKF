import { useState, useEffect } from "react";
import { DEV_SCENARIO } from "../../../lib/scenarios";
import { useTypingEffect, useDelayedAction } from "../../../lib/simulation";
import SystemBadge from "../../shared/SystemBadge";

interface IDEChatPanelProps {
  onComplete: () => void;
}

const FILE_TREE = [
  { name: "src", indent: 0, isDir: true },
  { name: "routes", indent: 1, isDir: true },
  { name: "users.ts", indent: 2, isDir: false, active: true },
  { name: "auth.ts", indent: 2, isDir: false },
  { name: "products.ts", indent: 2, isDir: false },
  { name: "db", indent: 1, isDir: true },
  { name: "index.ts", indent: 2, isDir: false },
  { name: "models.ts", indent: 2, isDir: false },
  { name: "package.json", indent: 0, isDir: false },
  { name: "tsconfig.json", indent: 0, isDir: false },
];

function CodeEditor({ code }: { code: string }) {
  const lines = code.split("\n");
  return (
    <div className="flex-1 overflow-auto font-mono text-[13px] leading-6 bg-[#1e1e1e]">
      <div className="flex">
        {/* Line numbers */}
        <div className="select-none text-right pr-4 pl-4 py-3 text-gray-600 bg-[#1e1e1e] border-r border-gray-800">
          {lines.map((_, i) => (
            <div key={i}>{i + 1}</div>
          ))}
        </div>
        {/* Code content */}
        <div className="py-3 pl-4 pr-6 text-gray-300 whitespace-pre overflow-x-auto flex-1">
          {lines.map((line, i) => (
            <div key={i} className={line.includes("TODO") ? "bg-amber-900/30" : ""}>
              {highlightTS(line)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function highlightTS(line: string): React.ReactNode {
  // Simple syntax highlighting for TypeScript
  return line
    .split(/(\/\/.*$|'[^']*'|"[^"]*"|`[^`]*`|\b(?:import|from|export|default|const|async|await|if|return)\b|(?:router|express|db|req|res|user))/gm)
    .map((part, i) => {
      if (!part) return null;
      if (part.startsWith("//"))
        return <span key={i} className="text-green-500">{part}</span>;
      if (part.startsWith("'") || part.startsWith('"') || part.startsWith("`"))
        return <span key={i} className="text-amber-300">{part}</span>;
      if (/^(import|from|export|default|const|async|await|if|return)$/.test(part))
        return <span key={i} className="text-purple-400">{part}</span>;
      if (/^(router|express|db|req|res|user)$/.test(part))
        return <span key={i} className="text-sky-300">{part}</span>;
      return <span key={i}>{part}</span>;
    });
}

function renderCopilotMarkdown(text: string): React.ReactNode {
  // Split by code blocks
  const parts = text.split(/(```[\s\S]*?```)/g);
  return parts.map((part, i) => {
    if (part.startsWith("```")) {
      // Extract code content (remove ``` markers and optional language tag)
      const codeContent = part
        .replace(/^```\w*\n?/, "")
        .replace(/\n?```$/, "");
      return (
        <pre
          key={i}
          className="bg-gray-900 border border-gray-700 rounded-md p-3 my-2 text-[12px] leading-5 text-gray-300 overflow-x-auto"
        >
          {codeContent}
        </pre>
      );
    }
    // Render markdown-ish text: bold and inline code
    const segments = part.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
    return (
      <span key={i}>
        {segments.map((seg, j) => {
          if (seg.startsWith("**") && seg.endsWith("**"))
            return <strong key={j} className="text-white font-semibold">{seg.slice(2, -2)}</strong>;
          if (seg.startsWith("`") && seg.endsWith("`"))
            return <code key={j} className="bg-gray-700 text-amber-300 px-1 py-0.5 rounded text-[11px]">{seg.slice(1, -1)}</code>;
          return <span key={j}>{seg}</span>;
        })}
      </span>
    );
  });
}

export default function IDEChatPanel({ onComplete }: IDEChatPanelProps) {
  const [showQuestion, setShowQuestion] = useState(false);
  const [typingActive, setTypingActive] = useState(false);
  const [showToast, setShowToast] = useState(false);

  const { displayed, done: typingDone } = useTypingEffect(
    DEV_SCENARIO.copilotResponse,
    typingActive,
    8
  );

  const toastDelay = useDelayedAction(1500);

  // Show question after initial delay
  useEffect(() => {
    const timer = setTimeout(() => setShowQuestion(true), 600);
    return () => clearTimeout(timer);
  }, []);

  // Start typing Copilot response after question appears
  useEffect(() => {
    if (!showQuestion) return;
    const timer = setTimeout(() => setTypingActive(true), 800);
    return () => clearTimeout(timer);
  }, [showQuestion]);

  // Show toast when typing finishes
  useEffect(() => {
    if (typingDone && !showToast) {
      toastDelay.trigger();
    }
  }, [typingDone, showToast, toastDelay]);

  // When toast delay completes, show toast and schedule onComplete
  useEffect(() => {
    if (toastDelay.complete && !showToast) {
      setShowToast(true);
    }
  }, [toastDelay.complete, showToast]);

  // Fire onComplete after toast is visible
  useEffect(() => {
    if (!showToast) return;
    const timer = setTimeout(() => onComplete(), 2000);
    return () => clearTimeout(timer);
  }, [showToast, onComplete]);

  return (
    <div className="rounded-lg overflow-hidden border border-gray-700 shadow-2xl bg-[#1e1e1e] flex flex-col h-[600px]">
      {/* Title bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-[#323233] border-b border-gray-700">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-red-500" />
          <span className="w-3 h-3 rounded-full bg-amber-500" />
          <span className="w-3 h-3 rounded-full bg-green-500" />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-400 font-mono">users.ts</span>
          <span className="text-gray-600 mx-1">-</span>
          <SystemBadge system="vscode" />
        </div>
        <div className="w-16" />
      </div>

      <div className="flex flex-1 min-h-0">
        {/* Sidebar - File tree */}
        <div className="w-52 bg-[#252526] border-r border-gray-700 py-2 overflow-y-auto shrink-0">
          <div className="px-3 py-1 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
            Explorer
          </div>
          {FILE_TREE.map((item, i) => (
            <div
              key={i}
              className={`flex items-center gap-1.5 px-3 py-0.5 text-[13px] cursor-default ${
                item.active
                  ? "bg-[#37373d] text-white"
                  : "text-gray-400 hover:bg-[#2a2d2e]"
              }`}
              style={{ paddingLeft: `${12 + item.indent * 12}px` }}
            >
              {item.isDir ? (
                <svg className="w-4 h-4 text-gray-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              ) : (
                <svg className="w-4 h-4 text-blue-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              )}
              <span className="truncate">{item.name}</span>
            </div>
          ))}
        </div>

        {/* Code editor */}
        <CodeEditor code={DEV_SCENARIO.codeFile} />

        {/* Chat panel */}
        <div className="w-80 bg-[#1e1e1e] border-l border-gray-700 flex flex-col shrink-0">
          {/* Chat header */}
          <div className="px-3 py-2 border-b border-gray-700 flex items-center gap-2">
            <svg className="w-4 h-4 text-purple-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
            </svg>
            <span className="text-sm font-semibold text-gray-300">Copilot Chat</span>
          </div>

          {/* Chat messages */}
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {showQuestion && (
              <div className="flex gap-2 animate-fade-in">
                {/* User avatar */}
                <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
                  D
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] text-gray-500 mb-0.5">You</p>
                  <p className="text-sm text-gray-200 leading-relaxed">
                    {DEV_SCENARIO.question}
                  </p>
                </div>
              </div>
            )}

            {typingActive && (
              <div className="flex gap-2">
                {/* Copilot avatar */}
                <div className="w-7 h-7 rounded-full bg-purple-600 flex items-center justify-center shrink-0">
                  <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
                  </svg>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-[11px] text-gray-500 mb-0.5">Copilot</p>
                  <div className="text-sm text-gray-300 leading-relaxed">
                    {renderCopilotMarkdown(displayed)}
                    {!typingDone && (
                      <span className="inline-block w-2 h-4 bg-gray-400 animate-pulse ml-0.5 align-middle" />
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Toast notification */}
      {showToast && (
        <div className="absolute bottom-6 right-6 flex items-center gap-2 bg-[#1e1e1e] border border-green-600 rounded-lg px-4 py-3 shadow-lg animate-slide-in z-10">
          <svg className="w-5 h-5 text-green-400 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <div>
            <p className="text-sm text-gray-200 font-medium">AKF sidecar generated</p>
            <p className="text-xs text-gray-400 font-mono">caching-strategy.akf</p>
          </div>
        </div>
      )}
    </div>
  );
}
