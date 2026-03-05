interface CodeBlockProps {
  code: string;
  language?: string;
  filename?: string;
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function highlightJSON(json: string): string {
  const escaped = escapeHtml(json);
  return escaped.replace(
    /(&quot;(?:\\u[a-fA-F0-9]{4}|\\[^u]|[^\\&])*&quot;(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
    (match) => {
      let cls = 'text-emerald-400'; // number
      if (/^&quot;/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'text-sky-400'; // key
        } else {
          cls = 'text-amber-300'; // string
        }
      } else if (/true|false/.test(match)) {
        cls = 'text-purple-400'; // boolean
      } else if (/null/.test(match)) {
        cls = 'text-gray-500'; // null
      }
      return `<span class="${cls}">${match}</span>`;
    }
  );
}

function highlightPython(code: string): string {
  let result = code
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Comments
  result = result.replace(/(#.*$)/gm, '<span class="text-gray-500">$1</span>');
  // Strings (double and single quoted)
  result = result.replace(/("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g, '<span class="text-amber-300">$1</span>');
  // Keywords
  result = result.replace(/\b(import|from|as|def|class|return|if|else|elif|for|in|while|with|try|except|finally|raise|yield|lambda|and|or|not|is|None|True|False|print)\b/g, '<span class="text-purple-400">$1</span>');
  // Numbers
  result = result.replace(/\b(\d+\.?\d*)\b/g, '<span class="text-emerald-400">$1</span>');

  return result;
}

function highlightTS(code: string): string {
  let result = code
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Comments
  result = result.replace(/(\/\/.*$)/gm, '<span class="text-gray-500">$1</span>');
  // Strings
  result = result.replace(/(["'`](?:[^"'`\\]|\\.)*["'`])/g, '<span class="text-amber-300">$1</span>');
  // Keywords
  result = result.replace(/\b(import|from|export|const|let|var|function|return|if|else|for|while|new|this|class|extends|interface|type|async|await|true|false|null|undefined|console)\b/g, '<span class="text-purple-400">$1</span>');
  // Numbers
  result = result.replace(/\b(\d+\.?\d*)\b/g, '<span class="text-emerald-400">$1</span>');

  return result;
}

function highlightBash(code: string): string {
  let result = code
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');

  // Comments
  result = result.replace(/(#.*$)/gm, '<span class="text-gray-500">$1</span>');
  // Strings
  result = result.replace(/("(?:[^"\\]|\\.)*")/g, '<span class="text-amber-300">$1</span>');
  // Flags
  result = result.replace(/(\s)(--?\w[\w-]*)/g, '$1<span class="text-sky-400">$2</span>');
  // Commands at line start
  result = result.replace(/^(\w[\w-]*)/gm, '<span class="text-emerald-400">$1</span>');

  return result;
}

function highlight(code: string, language?: string): string {
  switch (language) {
    case 'json':
      return highlightJSON(code);
    case 'python':
      return highlightPython(code);
    case 'typescript':
      return highlightTS(code);
    case 'bash':
      return highlightBash(code);
    default: {
      return code
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    }
  }
}

export default function CodeBlock({ code, language, filename }: CodeBlockProps) {
  const highlighted = highlight(code, language);

  return (
    <div className="rounded-lg overflow-hidden border border-gray-800">
      {filename && (
        <div className="flex items-center justify-between px-4 py-2.5 bg-gray-800 border-b border-gray-700">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
            <span className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
          </div>
          <span className="text-xs text-gray-400 font-mono">{filename}</span>
        </div>
      )}
      <pre
        className="p-4 text-[13px] leading-relaxed overflow-x-auto bg-gray-900 text-gray-300 font-mono"
        dangerouslySetInnerHTML={{ __html: highlighted }}
      />
    </div>
  );
}
