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
