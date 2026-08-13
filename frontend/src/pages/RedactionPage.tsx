import { useState, useMemo } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import ConfidenceBar from '../components/ConfidenceBar';
import StatusChip from '../components/StatusChip';
import { commitRedactions } from '../services/api';
import type { PIIEntity, UploadResponse } from '../types';

const FILTER_TABS = ['ALL', 'PERSON', 'EMAIL', 'PHONE', 'SSN', 'CREDIT_CARD', 'DOB', 'IP_ADDRESS', 'COMPANY', 'ADDRESS'];

const TYPE_LABELS: Record<string, string> = {
  PERSON: 'PERSON',
  EMAIL: 'EMAIL',
  PHONE: 'PHONE',
  SSN: 'SSN',
  CREDIT_CARD: 'CC#',
  DOB: 'DOB',
  IP_ADDRESS: 'IP',
  COMPANY: 'ORG',
  ADDRESS: 'ADDR',
};

export default function RedactionPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { id: jobId } = useParams<{ id: string }>();
  const data = location.state as UploadResponse | undefined;

  const [activeFilter, setActiveFilter] = useState('ALL');
  const [entities, setEntities] = useState<PIIEntity[]>(data?.entities ?? []);
  const [isCommitting, setIsCommitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filteredEntities = useMemo(() => {
    if (activeFilter === 'ALL') return entities;
    return entities.filter((e) => e.type === activeFilter);
  }, [entities, activeFilter]);

  // Get counts for tabs
  const typeCounts = useMemo(() => {
    const counts: Record<string, number> = { ALL: entities.length };
    for (const entity of entities) {
      counts[entity.type] = (counts[entity.type] || 0) + 1;
    }
    return counts;
  }, [entities]);

  // Only show tabs that have entities
  const visibleTabs = FILTER_TABS.filter(
    (tab) => tab === 'ALL' || (typeCounts[tab] && typeCounts[tab] > 0)
  );

  const handleCommit = async () => {
    if (!jobId) return;
    setIsCommitting(true);
    setError(null);

    try {
      const result = await commitRedactions(jobId, entities);
      navigate(`/release/${jobId}`, { state: result });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Redaction failed');
    } finally {
      setIsCommitting(false);
    }
  };

  const handleUpdateReplacement = (entityId: number, newReplacement: string) => {
    setEntities((prev) =>
      prev.map((e) => (e.id === entityId ? { ...e, replacement: newReplacement } : e))
    );
  };

  if (!data) {
    return (
      <div className="p-margin flex items-center justify-center min-h-full">
        <div className="border-2 border-ink p-8 bg-fresh-paper text-center">
          <span className="material-symbols-outlined text-5xl text-outline mb-4 block">folder_off</span>
          <h2 className="font-headline text-headline-md uppercase mb-2">NO ACTIVE CASE</h2>
          <p className="font-code text-code-sm text-outline mb-6">
            Upload a document to begin redaction analysis.
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

  return (
    <div className="p-margin relative min-h-full">
      {/* Header */}
      <header className="mb-gutter flex flex-col sm:flex-row justify-between items-start gap-4 border-b-2 border-ink pb-4">
        <div>
          <h2 className="font-headline text-headline-lg text-ink uppercase">
            REDACTION WORKSHEET — CASE #{jobId?.toUpperCase()}
          </h2>
          <div className="mt-2 text-on-surface-variant font-code text-code-sm">
            GENERATED: {new Date().toISOString().slice(0, 19)}Z | FILE: {data.filename}
          </div>
        </div>
        <StatusChip
          label={`ENTITIES FOUND: ${entities.length} — TYPES: ${Object.keys(typeCounts).length - 1}`}
          variant="danger"
          rotation={2}
        />
      </header>

      {/* Document Container */}
      <div className="border border-ink bg-fresh-paper relative pb-16 mt-10 shadow-[4px_4px_0px_rgba(28,27,25,0.1)]">
        {/* Folder Tabs */}
        <div className="flex flex-wrap absolute -top-8 left-0">
          {visibleTabs.map((tab) => (
            <button
              key={tab}
              className={`
                px-4 md:px-6 py-2 font-label text-label-caps font-bold
                border border-ink transition-colors text-sm
                ${
                  activeFilter === tab
                    ? 'folder-tab-active bg-fresh-paper text-ink border-b-0 h-9'
                    : 'bg-surface-dim text-olive hover:bg-surface-container-high h-8 mt-1'
                }
                ${tab !== visibleTabs[0] ? 'border-l-0' : ''}
              `}
              onClick={() => setActiveFilter(tab)}
            >
              {TYPE_LABELS[tab] || tab}
              {typeCounts[tab] ? ` (${typeCounts[tab]})` : ''}
            </button>
          ))}
        </div>

        {/* Ledger Table */}
        <div className="w-full pt-4 px-4 min-h-[400px]">
          {/* Table Header */}
          <div className="hidden md:grid grid-cols-12 gap-4 pb-2 border-b-2 border-ink font-label text-label-caps font-bold">
            <div className="col-span-1 text-center">ID</div>
            <div className="col-span-2">TYPE</div>
            <div className="col-span-4">ORIGINAL</div>
            <div className="col-span-3">REPLACEMENT</div>
            <div className="col-span-2">CONFIDENCE</div>
          </div>

          {/* Table Rows */}
          {filteredEntities.length === 0 ? (
            <div className="py-12 text-center">
              <span className="material-symbols-outlined text-4xl text-outline mb-2 block">search_off</span>
              <p className="font-code text-code-sm text-outline">
                No entities found for this filter.
              </p>
            </div>
          ) : (
            filteredEntities.map((entity) => (
              <div
                key={entity.id}
                className={`
                  grid grid-cols-1 md:grid-cols-12 gap-2 md:gap-4
                  py-3 border-b border-dashed border-outline-variant
                  ledger-row items-center font-code text-code-sm
                  ${entity.confidence < 0.70 ? 'bg-[#ffdad4]/20' : ''}
                `}
              >
                {/* ID */}
                <div className="col-span-1 text-center text-outline hidden md:block">
                  {String(entity.id).padStart(3, '0')}
                </div>

                {/* Type */}
                <div className="md:col-span-2 flex items-center gap-2">
                  <span className="md:hidden font-label text-label-caps text-outline">
                    #{String(entity.id).padStart(3, '0')}
                  </span>
                  <span className="border border-olive text-olive px-2 py-0.5 text-xs font-bold uppercase">
                    {TYPE_LABELS[entity.type] || entity.type}
                  </span>
                </div>

                {/* Original */}
                <div className="md:col-span-4 flex items-center gap-1">
                  <span className="redaction-block">{entity.original}</span>
                  {entity.confidence < 0.70 && (
                    <span
                      className="material-symbols-outlined text-stamp-red text-sm ml-1"
                      title="Review Recommended"
                    >
                      warning
                    </span>
                  )}
                </div>

                {/* Replacement */}
                <div className="md:col-span-3">
                  <input
                    className="w-full bg-transparent border-0 border-b border-outline-variant p-0 font-code text-code-sm text-outline focus:ring-0 focus:outline-none focus:border-ink px-1 py-0.5"
                    type="text"
                    value={entity.replacement}
                    onChange={(e) => handleUpdateReplacement(entity.id, e.target.value)}
                  />
                </div>

                {/* Confidence */}
                <div className="md:col-span-2">
                  <ConfidenceBar value={entity.confidence * 100} />
                </div>
              </div>
            ))
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mx-4 mt-4 border-2 border-stamp-red bg-error-container p-3 font-code text-code-sm text-on-error-container">
            <span className="material-symbols-outlined text-sm mr-2 align-middle">error</span>
            {error}
          </div>
        )}

        {/* Action Buttons */}
        <div className="absolute bottom-4 right-4 flex gap-4">
          <button
            className="border-2 border-ink px-6 py-2 font-label text-label-caps font-bold bg-fresh-paper hover:bg-ink hover:text-fresh-paper transition-colors"
            onClick={() => navigate('/')}
          >
            BACK TO INTAKE
          </button>
          <button
            className="border-2 border-stamp-red px-6 py-2 font-label text-label-caps font-bold bg-fresh-paper text-stamp-red hover:bg-stamp-red hover:text-fresh-paper transition-colors shadow-[2px_2px_0px_#A63D2F] active:translate-y-0.5 active:shadow-[0px_0px_0px_#A63D2F]"
            onClick={handleCommit}
            disabled={isCommitting || entities.length === 0}
          >
            {isCommitting ? (
              <>
                <span className="cursor-blink mr-1">█</span>
                COMMITTING...
              </>
            ) : (
              'COMMIT REDACTIONS'
            )}
          </button>
        </div>
      </div>

      {/* Stats footer */}
