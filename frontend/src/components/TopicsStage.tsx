import React, { useMemo, useState } from 'react';
import { ArrowLeft, ArrowRight, Check, FileText, Plus, Search, Youtube } from 'lucide-react';
import { SourceType } from '../types';

interface TopicsStageProps {
  sourceType: SourceType | null;
  sourceTitle: string;
  extractedTopics: string[];
  selectedTopics: string[];
  onChangeTopics: (topics: string[]) => void;
  onBack: () => void;
  onNext: () => void;
}

const TopicsStage: React.FC<TopicsStageProps> = ({
  sourceType,
  sourceTitle,
  extractedTopics,
  selectedTopics,
  onChangeTopics,
  onBack,
  onNext,
}) => {
  const [availableTopics, setAvailableTopics] = useState<string[]>(extractedTopics);
  const [search, setSearch] = useState('');
  const [customTopic, setCustomTopic] = useState('');

  const filteredTopics = useMemo(() => {
    const q = search.trim().toLowerCase();
    return q ? availableTopics.filter((t) => t.toLowerCase().includes(q)) : availableTopics;
  }, [availableTopics, search]);

  const toggleTopic = (topic: string) => {
    if (selectedTopics.includes(topic)) {
      onChangeTopics(selectedTopics.filter((t) => t !== topic));
    } else {
      onChangeTopics([...selectedTopics, topic]);
    }
  };

  const handleAddCustom = (e: React.FormEvent) => {
    e.preventDefault();
    const cleaned = customTopic.trim();
    if (!cleaned) return;
    if (!availableTopics.includes(cleaned)) {
      setAvailableTopics((prev) => [...prev, cleaned]);
    }
    if (!selectedTopics.includes(cleaned)) {
      onChangeTopics([...selectedTopics, cleaned]);
    }
    setCustomTopic('');
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="space-y-2">
        <div className="inline-flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900 px-3 py-1 text-xs text-slate-300">
          {sourceType === 'youtube' ? (
            <Youtube className="h-3.5 w-3.5 text-cyan-400" />
          ) : (
            <FileText className="h-3.5 w-3.5 text-cyan-400" />
          )}
          <span className="max-w-xs truncate font-medium">{sourceTitle || 'Study Material'}</span>
        </div>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">Select Topics</h1>
        <p className="text-sm text-slate-400">
          Choose which extracted topics to include in your practice quiz ({selectedTopics.length} selected).
        </p>
      </div>

      <div className="surface-card space-y-5 p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter topics..."
              aria-label="Filter topics"
              className="w-full rounded-xl border border-slate-700 bg-slate-950/70 py-2 pl-9 pr-3 text-sm text-white placeholder-slate-500 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
            />
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => onChangeTopics(availableTopics)}
              className="btn-secondary px-3 py-2 text-xs"
            >
              Select all
            </button>
            <button
              type="button"
              onClick={() => onChangeTopics([])}
              className="btn-secondary px-3 py-2 text-xs"
            >
              Clear
            </button>
          </div>
        </div>

        <div className="grid gap-2.5 sm:grid-cols-2">
          {filteredTopics.map((topic) => {
            const selected = selectedTopics.includes(topic);
            return (
              <button
                key={topic}
                type="button"
                aria-pressed={selected}
                onClick={() => toggleTopic(topic)}
                className={`flex items-center justify-between rounded-xl border px-4 py-3 text-left text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 ${
                  selected
                    ? 'border-cyan-400 bg-cyan-500/10 text-white'
                    : 'border-slate-800 bg-slate-950/50 text-slate-300 hover:border-slate-700 hover:text-white'
                }`}
              >
                <span className="truncate pr-3">{topic}</span>
                <span
                  className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md border ${
                    selected
                      ? 'border-cyan-400 bg-cyan-500 text-slate-950'
                      : 'border-slate-600 bg-transparent'
                  }`}
                >
                  {selected && <Check className="h-3.5 w-3.5 stroke-[3]" />}
                </span>
              </button>
            );
          })}
        </div>

        <form onSubmit={handleAddCustom} className="flex gap-2 border-t border-slate-800 pt-4">
          <input
            type="text"
            value={customTopic}
            onChange={(e) => setCustomTopic(e.target.value)}
            placeholder="Add a custom topic..."
            aria-label="Add a custom topic"
            className="flex-1 rounded-xl border border-slate-700 bg-slate-950/70 px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-400/30"
          />
          <button type="submit" className="btn-secondary">
            <Plus className="h-4 w-4" />
            <span>Add</span>
          </button>
        </form>
      </div>

      <div className="flex items-center justify-between">
        <button type="button" onClick={onBack} className="btn-secondary">
          <ArrowLeft className="h-4 w-4" />
          <span>Back</span>
        </button>
        <button
          type="button"
          disabled={selectedTopics.length === 0}
          onClick={onNext}
          className="btn-primary"
        >
          <span>Continue</span>
          <ArrowRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
};

export default TopicsStage;
