import React, { useRef, useState } from 'react';
import { FileText, Loader2, Upload, Youtube } from 'lucide-react';
import toast from 'react-hot-toast';
import { extractErrorMessage, ingestYouTubeVideo, uploadPdfDocument } from '../api';
import { SourceType } from '../types';

interface HomeStageProps {
  onIngested: (payload: {
    sourceType: SourceType;
    sourceTitle: string;
    docId: string;
    topics: string[];
  }) => void;
}

const HomeStage: React.FC<HomeStageProps> = ({ onIngested }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);

  const [ytUrl, setYtUrl] = useState('');
  const [ytLoading, setYtLoading] = useState(false);
  const [ytError, setYtError] = useState<string | null>(null);

  const isBusy = pdfLoading || ytLoading;

  const handlePdfFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf') && file.type !== 'application/pdf') {
      const msg = 'Please select a valid PDF file.';
      setPdfError(msg);
      toast.error(msg);
      return;
    }

    setPdfError(null);
    setPdfLoading(true);
    try {
      const res = await uploadPdfDocument(file);
      toast.success(`Extracted ${res.topics.length} topics from PDF`);
      onIngested({
        sourceType: 'pdf',
        sourceTitle: file.name,
        docId: res.doc_id,
        topics: res.topics,
      });
    } catch (err) {
      const msg = extractErrorMessage(err, 'Failed to process PDF.');
      setPdfError(msg);
      toast.error(msg);
    } finally {
      setPdfLoading(false);
    }
  };

  const handleYouTubeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = ytUrl.trim();
    if (!trimmed) {
      const msg = 'Please paste a YouTube video URL.';
      setYtError(msg);
      toast.error(msg);
      return;
    }

    setYtError(null);
    setYtLoading(true);
    try {
      const res = await ingestYouTubeVideo(trimmed);
      toast.success(`Extracted ${res.topics.length} topics from video`);
      onIngested({
        sourceType: 'youtube',
        sourceTitle: res.title,
        docId: res.doc_id,
        topics: res.topics,
      });
    } catch (err) {
      const msg = extractErrorMessage(err, 'Failed to fetch YouTube transcript.');
      setYtError(msg);
      toast.error(msg);
    } finally {
      setYtLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-10">
      <div className="space-y-3 text-center">
        <h1 className="text-3xl font-bold tracking-tight text-white sm:text-5xl">
          Turn study material into{' '}
          <span className="text-cyan-400">focused practice tests</span>
        </h1>
        <p className="mx-auto max-w-2xl text-sm text-slate-400 sm:text-base">
          Upload a PDF document or paste a YouTube lecture link. MindQ extracts key topics,
          builds grounded questions with source references, and tracks your accuracy.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Card 1: Upload a PDF */}
        <section className="surface-card flex flex-col justify-between p-6 transition-colors hover:border-slate-700">
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400">
                <FileText className="h-5 w-5" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Upload a PDF</h2>
                <p className="text-xs text-slate-400">Notes, slides, chapters, or study guides</p>
              </div>
            </div>

            <button
              type="button"
              disabled={isBusy}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                if (!isBusy) setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                if (isBusy) return;
                const file = e.dataTransfer.files?.[0];
                if (file) handlePdfFile(file);
              }}
              className={`flex w-full flex-col items-center justify-center rounded-xl border-2 border-dashed px-4 py-10 text-center transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
                dragOver
                  ? 'border-cyan-400 bg-cyan-500/10'
                  : 'border-slate-700 bg-slate-950/50 hover:border-cyan-500/60'
              } disabled:cursor-not-allowed disabled:opacity-60`}
            >
              {pdfLoading ? (
                <>
                  <Loader2 className="mb-3 h-8 w-8 animate-spin text-cyan-400" />
                  <span className="text-sm font-medium text-white">Analyzing PDF &amp; extracting topics...</span>
                  <span className="mt-1 text-xs text-slate-400">Indexing pages for retrieval</span>
                </>
              ) : (
                <>
                  <Upload className="mb-3 h-8 w-8 text-cyan-400" />
                  <span className="text-sm font-medium text-white">
                    Drop a PDF here or click to browse
                  </span>
                  <span className="mt-1 text-xs text-slate-400">Each question cites its source page</span>
                </>
              )}
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handlePdfFile(file);
                e.target.value = '';
              }}
            />
          </div>

          {pdfError && (
            <p role="alert" className="mt-4 rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
              {pdfError}
            </p>
          )}
        </section>

        {/* Card 2: Paste a YouTube link */}
        <section className="surface-card flex flex-col justify-between p-6 transition-colors hover:border-slate-700">
          <form onSubmit={handleYouTubeSubmit} className="flex h-full flex-col justify-between space-y-4">
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/10 text-cyan-400">
                  <Youtube className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-white">Paste a YouTube link</h2>
                  <p className="text-xs text-slate-400">Turn any YouTube video into practice tests</p>
                </div>
              </div>

              <div className="space-y-2 pt-2">
                <label htmlFor="youtube-url-input" className="block text-xs font-medium text-slate-300">
                  YouTube Video URL
                </label>
                <input
                  id="youtube-url-input"
                  type="url"
                  value={ytUrl}
                  onChange={(e) => setYtUrl(e.target.value)}
                  disabled={isBusy}
                  placeholder="https://www.youtube.com/watch?v=..."
                  className="w-full rounded-xl border border-slate-700 bg-slate-950/70 px-4 py-3 text-sm text-white placeholder-slate-500 transition-colors focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/30 disabled:opacity-60"
                />
                <p className="text-xs text-slate-400">
                  Requires video captions. Questions include clickable-style timestamp references.
                </p>
              </div>
            </div>

            <div className="space-y-3 pt-2">
              {ytError && (
                <p role="alert" className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">
                  {ytError}
                </p>
              )}

              <button type="submit" disabled={isBusy} className="btn-primary w-full">
                {ytLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Fetching transcript...</span>
                  </>
                ) : (
                  <span>Extract Topics</span>
                )}
              </button>
            </div>
          </form>
        </section>
      </div>
    </div>
  );
};

export default HomeStage;
