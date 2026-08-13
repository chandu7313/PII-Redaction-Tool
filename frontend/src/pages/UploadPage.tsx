import { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import StatusChip from '../components/StatusChip';
import StampButton from '../components/StampButton';
import { uploadDocument } from '../services/api';

export default function UploadPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile?.name.endsWith('.docx')) {
      setFile(droppedFile);
      setError(null);
    } else {
      setError('Only .docx files are accepted');
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile?.name.endsWith('.docx')) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Only .docx files are accepted');
    }
  }, []);

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    try {
      const result = await uploadDocument(file);
      // Navigate to redaction page with the result
      navigate(`/redaction/${result.job_id}`, { state: result });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="p-margin flex gap-gutter justify-center min-h-full">
      {/* Central Dossier */}
      <div className="w-full max-w-4xl paper-stack bg-fresh-paper border border-ink p-6 md:p-8 flex flex-col">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start gap-4 border-b-2 border-ink pb-4 mb-8">
          <div>
            <h2 className="font-headline text-headline-md uppercase">
              Initialize Dossier
            </h2>
            <p className="font-code text-code-sm text-outline mt-2">
              REF_ID: {Math.random().toString(36).substring(2, 8).toUpperCase()}-A // CLASSIFIED
            </p>
          </div>
          <StatusChip
            label={file ? 'FILE LOADED' : 'STATUS: PENDING'}
            variant={file ? 'success' : 'danger'}
            rotation={-2}
          />
        </div>

        {/* Content Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-gutter flex-1">
          {/* Upload Zone */}
          <div
            className={`
              md:col-span-8 flex flex-col
              border-2 border-dashed border-ink
              p-8 items-center justify-center
              bg-surface-bright ruled-line
              relative group cursor-pointer
              transition-colors min-h-[280px]
              ${isDragging ? 'upload-zone-active' : 'hover:bg-surface-container-lowest'}
              ${file ? 'border-olive' : ''}
            `}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".docx"
              className="hidden"
              onChange={handleFileSelect}
            />

            {file ? (
              <>
                <span className="material-symbols-outlined text-5xl mb-4 text-olive">
                  task
                </span>
                <p className="font-headline text-headline-md text-center mb-2">
                  {file.name}
                </p>
                <p className="font-code text-code-sm text-outline text-center">
                  {(file.size / 1024).toFixed(1)} KB — READY FOR PROCESSING
                </p>
                <button
                  className="mt-4 font-code text-code-sm text-stamp-red border border-stamp-red px-3 py-1 hover:bg-stamp-red hover:text-fresh-paper transition-colors"
                  onClick={(e) => {
                    e.stopPropagation();
                    setFile(null);
                  }}
                >
                  REMOVE FILE
                </button>
              </>
            ) : (
              <>
                <span className="material-symbols-outlined text-5xl mb-4 text-ink">
                  upload_file
                </span>
                <p className="font-headline text-headline-md text-center mb-2">
                  DROP DOCX HERE
                </p>
                <p className="font-code text-code-sm text-outline text-center">
                  OR CLICK TO BROWSE LOCAL FILES
                </p>
              </>
            )}

            <div className="absolute bottom-3 right-3 text-xs font-code text-outline">
              MAX SIZE: 50MB
            </div>
          </div>

          {/* Side Metadata / Intake Form */}
          <div className="md:col-span-4 flex flex-col gap-4">
            <div className="border border-ink p-4 bg-surface-bright">
              <label className="block font-label text-label-caps mb-1 uppercase">
                Operative ID
              </label>
              <input
                className="w-full bg-transparent border-0 border-b border-ink p-0 font-code text-code-sm focus:ring-0 focus:outline-none px-1 py-1"
                type="text"
                value="ANALYST_404"
                readOnly
              />
            </div>

            <div className="border border-ink p-4 bg-surface-bright">
              <label className="block font-label text-label-caps mb-1 uppercase">
                Clearance Level
              </label>
              <input
                className="w-full bg-transparent border-0 border-b border-ink p-0 font-code text-code-sm focus:ring-0 focus:outline-none px-1 py-1"
                type="text"
                value="TOP SECRET // SCI"
                readOnly
              />
            </div>

            <div className="border border-ink p-4 bg-surface-bright flex-1">
              <label className="block font-label text-label-caps mb-1 uppercase">
                Intake Notes
              </label>
              <textarea
                className="w-full h-24 bg-transparent border-0 border-b border-ink p-0 font-code text-code-sm focus:ring-0 focus:outline-none resize-none px-1 py-1"
                placeholder="Enter preliminary redaction targets..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-4 border-2 border-stamp-red bg-error-container p-3 font-code text-code-sm text-on-error-container">
            <span className="material-symbols-outlined text-sm mr-2 align-middle">error</span>
            {error}
          </div>
        )}

        {/* Submit Button */}
        <div className="mt-8 flex justify-end">
          <StampButton
            variant={file ? 'primary' : 'default'}
            icon="visibility_off"
            rotation={1}
            disabled={!file || isUploading}
            onClick={handleUpload}
            className={!file ? 'opacity-50 cursor-not-allowed' : ''}
          >
            {isUploading ? (
              <>
                <span className="cursor-blink">█</span>
                PROCESSING...
              </>
            ) : (
              'Begin Redaction'
            )}
          </StampButton>
        </div>
      </div>

      {/* Right Sidebar — Recent Activity (desktop only) */}
      <div className="hidden xl:flex flex-col w-56 gap-gutter shrink-0">
        <div className="border border-ink p-4 bg-surface-bright paper-stack h-64">
          <h3 className="font-label text-label-caps border-b border-ink pb-2 mb-3 uppercase">
            Recent Activity
          </h3>
          <ul className="font-code text-code-sm space-y-2 text-outline">
            <li className="truncate">&gt; System initialized</li>
            <li className="truncate">&gt; Awaiting dossier</li>
            <li className="truncate">&gt; Clearance verified</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
