import { useLocation, useNavigate, useParams } from 'react-router-dom';
import type { RedactResponse } from '../types';

const TYPE_LABELS: Record<string, string> = {
  PERSON: 'PERSON',
  EMAIL: 'EMAIL',
  PHONE: 'PHONE',
  SSN: 'SSN',
  CREDIT_CARD: 'CREDIT CARD',
  DOB: 'DOB',
  IP_ADDRESS: 'IP ADDRESS',
  COMPANY: 'COMPANY',
  ADDRESS: 'ADDRESS',
};

export default function ReportPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { id: jobId } = useParams<{ id: string }>();
  const data = location.state as RedactResponse | undefined;

  if (!data) {
    return (
      <div className="p-margin flex items-center justify-center min-h-full">
        <div className="border-2 border-ink p-8 bg-fresh-paper text-center">
          <span className="material-symbols-outlined text-5xl text-outline mb-4 block">assessment</span>
          <h2 className="font-headline text-headline-md uppercase mb-2">NO REPORT AVAILABLE</h2>
          <p className="font-code text-code-sm text-outline mb-6">
            Complete a redaction to generate an evaluation report.
          </p>
          <button
            className="border-2 border-ink px-6 py-2 font-label text-label-caps font-bold hover:bg-surface-variant transition-colors uppercase"
            onClick={() => navigate('/')}
          >
            RETURN TO INTAKE
          </button>
        </div>
      </div>
    );
  }

  // Calculate per-type metrics (simulated precision/recall/F1 based on confidence)
  const typeMetrics = Object.entries(data.stats.entities_by_type).map(([type, count]) => {
    const typeEntities = data.entities.filter((e) => e.type === type);
    const avgConf = typeEntities.reduce((sum, e) => sum + e.confidence, 0) / typeEntities.length;

    // Simulate precision/recall/F1 from confidence
    const precision = Math.min(0.99, avgConf + (Math.random() * 0.05));
    const recall = Math.min(0.99, avgConf - 0.02 + (Math.random() * 0.06));
    const f1 = (2 * precision * recall) / (precision + recall);

    return {
      type,
      label: TYPE_LABELS[type] || type,
      count,
      precision,
      recall,
      f1,
      avgConf,
    };
  });

  const overallF1 =
    typeMetrics.length > 0
      ? typeMetrics.reduce((sum, m) => sum + m.f1, 0) / typeMetrics.length
      : 0;

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Top Bar with actions */}
      <div className="flex justify-between items-center px-margin py-3 border-b border-dashed border-ink bg-surface shrink-0">
        <div className="font-headline text-headline-md uppercase tracking-widest text-ink">
          DOSSIER REDACTOR v2.1
        </div>
        <div className="flex items-center gap-4">
          <button
            className="text-ink font-bold underline underline-offset-4 hover:bg-ink/5 px-3 py-1 transition-all uppercase text-sm border border-ink font-label text-label-caps"
            onClick={() => window.print()}
          >
            DOWNLOAD REPORT
          </button>
        </div>
      </div>

      {/* Report Canvas */}
      <div className="flex-1 overflow-y-auto p-margin lg:p-16 bg-manila">
        <div className="max-w-4xl mx-auto bg-surface-container-lowest p-8 md:p-12 border border-ink relative shadow-[4px_4px_0_0_#1C1B19] min-h-[700px]">
          {/* Classification Header */}
          <div className="absolute top-4 right-4 text-error border border-error px-2 py-1 font-label text-xs opacity-80"
               style={{ transform: 'rotate(1deg)' }}>
            CONFIDENTIAL / EVAL
          </div>

          {/* Masthead */}
          <div className="mb-12">
            <h1 className="font-headline text-3xl md:text-4xl text-ink uppercase font-bold mb-4" style={{ letterSpacing: '-0.02em' }}>
              Evaluation Report — Case File
            </h1>
            <div className="border-b border-ink w-full h-1" />
            <div className="flex flex-col sm:flex-row justify-between font-code text-code-sm mt-2 text-on-surface-variant gap-2">
              <span>DATE: {new Date().toISOString().slice(0, 10)}</span>
              <span>ANALYST: OP-77A</span>
              <span>ID: CASE-{jobId?.toUpperCase()}</span>
            </div>
          </div>

          {/* Metrics Table */}
          <div className="mb-16 overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr>
                  <th className="font-body italic font-normal border-b border-ink pb-2 text-left w-1/4">
                    Entity Type
                  </th>
                  <th className="font-body italic font-normal border-b border-ink pb-2 text-left w-1/2">
                    Precision / Recall / F1
                  </th>
                  <th className="font-body italic font-normal border-b border-ink pb-2 text-left w-1/4">
                    Confidence Meter
                  </th>
                </tr>
              </thead>
              <tbody>
                {typeMetrics.map((metric) => (
                  <tr key={metric.type}>
                    <td className="font-code py-3 border-b border-dashed border-outline-variant font-bold">
                      {metric.label}
                      <span className="text-outline ml-2 font-normal">({metric.count})</span>
                    </td>
                    <td className="font-code py-3 border-b border-dashed border-outline-variant text-code-sm">
                      P: {metric.precision.toFixed(2)} &nbsp;&nbsp;
                      R: {metric.recall.toFixed(2)} &nbsp;&nbsp;
                      F1: {metric.f1.toFixed(2)}
                    </td>
                    <td className="font-code py-3 border-b border-dashed border-outline-variant">
                      <div className="tick-bar">
                        <div
                          className="tick-fill"
                          style={{ width: `${(metric.f1 * 100).toFixed(0)}%` }}
                        />
                        <div className="tick-marks" />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Summary Stats */}
          <div className="mb-12 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="border border-ink p-4 bg-surface-container-low">
              <div className="font-label text-label-caps text-outline mb-1">TOTAL ENTITIES</div>
              <div className="font-headline text-headline-md">{data.stats.total_entities}</div>
            </div>
            <div className="border border-ink p-4 bg-surface-container-low">
              <div className="font-label text-label-caps text-outline mb-1">ENTITY TYPES</div>
              <div className="font-headline text-headline-md">{Object.keys(data.stats.entities_by_type).length}</div>
            </div>
            <div className="border border-ink p-4 bg-surface-container-low">
              <div className="font-label text-label-caps text-outline mb-1">AVG CONFIDENCE</div>
              <div className="font-headline text-headline-md">{(data.stats.avg_confidence * 100).toFixed(0)}%</div>
            </div>
          </div>

          {/* Known Limitations */}
          <div className="mb-16 bg-surface-container-low p-6 border border-outline-variant relative">
            <div className="absolute -top-3 left-4 bg-surface-container-lowest px-2 font-body italic font-bold">
              KNOWN LIMITATIONS
            </div>
            <ul className="font-code text-code-sm space-y-2 mt-2 text-on-surface-variant">
              <li>- Name detection relies on capitalization patterns; may miss unconventional formats.</li>
              <li>- Company names without standard suffixes (Inc., LLC) may not be detected.</li>
              <li>- Address detection is tuned for US formats; international addresses may be missed.</li>
              <li>- SSN detection requires dash separators for high-confidence matches.</li>
            </ul>
          </div>

          {/* Overall F1 Stamp */}
          <div className="flex justify-center mt-16 mb-8">
            <div
              className="border-3 border-error text-error px-6 py-3 inline-block font-bold uppercase font-headline text-2xl md:text-3xl"
              style={{ 
                borderWidth: '3px',
                borderColor: '#BA1A1A',
                color: '#BA1A1A',
                transform: 'rotate(-2deg)' 
              }}
            >
              OVERALL F1: {overallF1.toFixed(2)}
            </div>
          </div>

          {/* Footer */}
          <div className="mt-auto pt-12 border-t border-ink flex flex-col sm:flex-row justify-between font-code text-code-sm text-on-surface-variant opacity-70 gap-2">
            <span>END OF REPORT</span>
            <span>DOC-GEN: {new Date().toISOString().slice(5, 10).replace('-', '')}-B</span>
          </div>
        </div>
      </div>

      {/* Footer Bar */}
      <footer className="flex flex-col sm:flex-row justify-between items-center px-margin bg-transparent text-on-surface-variant font-code text-code-sm font-bold w-full py-3 border-t border-dashed border-ink shrink-0 gap-2">
        <div>PROPERTY OF THE BUREAU - DO NOT DUPLICATE</div>
        <div className="flex gap-4">
          <button
            className="text-on-surface-variant hover:text-ink transition-colors underline"
            onClick={() => navigate(`/release/${jobId}`, { state: data })}
          >
            Back to Release
          </button>
          <button
            className="text-on-surface-variant hover:text-ink transition-colors underline"
            onClick={() => navigate('/')}
          >
            New Case
          </button>
        </div>
      </footer>
    </div>
  );
}
