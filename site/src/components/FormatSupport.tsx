import SectionHeading from '../ui/SectionHeading';

const formats = [
  { format: '.akf', method: 'Native standalone', description: 'Pure AKF knowledge unit file' },
  { format: '.docx .xlsx .pptx', method: 'OOXML custom XML part', description: 'Embedded in Office documents' },
  { format: '.pdf', method: 'PDF metadata stream', description: 'Embedded in PDF metadata' },
  { format: '.html', method: 'JSON-LD <script>', description: 'application/akf+json script tag' },
  { format: '.md', method: 'YAML frontmatter', description: 'Structured frontmatter block' },
  { format: '.png .jpg', method: 'EXIF / XMP metadata', description: 'Image metadata fields' },
  { format: '.json', method: 'Reserved _akf key', description: 'Top-level _akf property' },
  { format: 'Everything else', method: 'Sidecar .akf.json', description: 'Companion file alongside the original' },
];

export default function FormatSupport() {
  return (
    <section id="formats" className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          title="Works with every format"
          subtitle="AKF embeds natively where possible, or travels as a sidecar."
        />
        <div className="overflow-x-auto rounded-xl border border-border-subtle">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-surface-overlay">
                <th className="px-6 py-3 text-xs font-semibold text-text-tertiary uppercase tracking-wider">Format</th>
                <th className="px-6 py-3 text-xs font-semibold text-text-tertiary uppercase tracking-wider">Embedding Method</th>
                <th className="px-6 py-3 text-xs font-semibold text-text-tertiary uppercase tracking-wider hidden sm:table-cell">Notes</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {formats.map((f) => (
                <tr key={f.format} className="bg-surface-raised hover:bg-surface-overlay transition-colors">
                  <td className="px-6 py-3.5 text-sm font-mono font-medium text-accent whitespace-nowrap">{f.format}</td>
                  <td className="px-6 py-3.5 text-sm text-text-primary">{f.method}</td>
                  <td className="px-6 py-3.5 text-sm text-text-secondary hidden sm:table-cell">{f.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
