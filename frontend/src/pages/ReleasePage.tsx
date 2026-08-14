import { useLocation, useNavigate, useParams } from 'react-router-dom';
import StampButton from '../components/StampButton';
import { downloadRedacted } from '../services/api';
import { useState } from 'react';
import type { RedactResponse } from '../types';

export default function ReleasePage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { id: jobId } = useParams<{ id: string }>();
  const data = location.state as RedactResponse | undefined;
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async () => {
    if (!jobId) return;
    setIsDownloading(true);
    setError(null);
    try {
      await downloadRedacted(jobId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
    } finally {
      setIsDownloading(false);
    }
  };

  if (!data) {
    return (
      <div className="p-margin flex items-center justify-center min-h-full">
        <div className="border-2 border-ink p-8 bg-fresh-paper text-center">
          <span className="material-symbols-outlined text-5xl text-outline mb-4 block">folder_off</span>
          <h2 className="font-headline text-headline-md uppercase mb-2">NO DOCUMENT AVAILABLE</h2>
          <p className="font-code text-code-sm text-outline mb-6">
            Complete the redaction process first.
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

  // Build a highlighted version of original text showing redacted spans
  const renderHighlightedText = (text: string) => {
    if (!data.entities || data.entities.length === 0) {
      return <p className="font-body text-body-md whitespace-pre-wrap">{text}</p>;
    }

    // Split text into paragraphs
    const paragraphs = text.split('\n');
    return (
      <div className="font-body text-body-md space-y-3 text-justify">
        {paragraphs.map((para, i) => {
          if (!para.trim()) return null;
          return <p key={i}>{para}</p>;
        })}
      </div>
    );
  };

  return (
    <div className="flex-1 overflow-y-auto p-margin flex flex-col items-center">
      <div className="w-full max-w-6xl mx-auto flex-1 flex flex-col">
        {/* Header */}
        <header className="mb-gutter text-center border-b border-ink pb-stack border-dashed">
          <h2 className="font-headline text-headline-lg uppercase text-ink tracking-tighter">
            DOCUMENT CLEARED FOR RELEASE
          </h2>
          <p className="font-code text-code-sm mt-2 text-on-surface-variant">
            REF: CASE-{jobId?.toUpperCase()} // CLEARANCE LEVEL 3
          </p>
        </header>

        {/* Document Split View */}
        <div className="flex-1 flex flex-col lg:flex-row w-full relative bg-surface-bright border border-outline shadow-[4px_4px_0px_#1C1B19] torn-edge mb-margin overflow-hidden">
          {/* Left Page: ORIGINAL */}
          <div className="flex-1 p-margin border-b lg:border-b-0 lg:border-r border-outline border-dashed relative">
            <div className="absolute top-4 left-4 border border-stamp-red text-stamp-red px-2 py-1 font-label text-label-caps uppercase opacity-70"
                 style={{ transform: 'rotate(-3deg)' }}>
              CONFIDENTIAL
            </div>
            <h3 className="font-headline text-headline-md text-center mb-6 border-b border-outline pb-2 w-full">
              ORIGINAL
            </h3>
            {renderHighlightedText(data.original_text)}
          </div>

          {/* Center crease */}
          <div className="hidden lg:block absolute inset-y-0 left-1/2 w-4 -ml-2 bg-gradient-to-r from-transparent via-black/5 to-transparent pointer-events-none" />

          {/* Right Page: REDACTED */}
          <div className="flex-1 p-margin relative bg-fresh-paper">
            <h3 className="font-headline text-headline-md text-center mb-6 border-b border-outline pb-2 w-full">
              REDACTED COPY
            </h3>
            {renderHighlightedText(data.redacted_text)}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-4 border-2 border-stamp-red bg-error-container p-3 font-code text-code-sm text-on-error-container text-center">
            <span className="material-symbols-outlined text-sm mr-2 align-middle">error</span>
            {error}
          </div>
        )}

        {/* Footer Actions */}
        <div className="mt-auto flex flex-col items-center justify-center pb-margin">
          <div className="relative stamp-ring w-full max-w-md flex flex-col items-center p-6 gap-4">
            <StampButton
              variant="primary"
              rotation={-2}
              onClick={handleDownload}
              disabled={isDownloading}
              className="shadow-[4px_4px_0px_#A63D2F]"
            >
              {isDownloading ? (
                <>
                  <span className="cursor-blink mr-1">█</span>
                  PREPARING...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined">download</span>
                  DOWNLOAD REDACTED DOCX
                </>
              )}
            </StampButton>

            <button
              className="border-2 border-ink px-6 py-2 font-label text-label-caps font-bold bg-fresh-paper hover:bg-surface-variant transition-colors uppercase"
              onClick={() => navigate(`/report/${jobId}`, { state: data })}
            >
              VIEW EVALUATION REPORT
            </button>
          </div>

          <p className="font-code text-code-sm text-stamp-red mt-4 border border-stamp-red px-4 py-1 uppercase tracking-widest bg-manila">
            STATUS: CLEARED FOR RELEASE — {data.entities.length} entities redacted
          </p>
        </div>
      </div>
    </div>
  );
}
