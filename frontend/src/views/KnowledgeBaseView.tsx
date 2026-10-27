import React, { useEffect, useState } from 'react';
import { 
  Database, 
  UploadCloud, 
  Search, 
  Trash2, 
  FileText, 
  Globe, 
  Brain, 
  Sparkles, 
  CheckCircle2, 
  AlertCircle,
  RefreshCw,
  ExternalLink
} from 'lucide-react';
import { api } from '../services/api';
import { KnowledgeDocument, KnowledgeSearchResult } from '../types';

export const KnowledgeBaseView: React.FC = () => {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<KnowledgeSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [uploadMsg, setUploadMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const docs = await api.listDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setUploading(true);
      setUploadMsg(null);
      const res = await api.uploadDocument(file);
      setUploadMsg({ type: 'success', text: `Indexed '${res.title}' into ${res.chunk_count} vector chunks.` });
      loadDocuments();
    } catch (err: any) {
      setUploadMsg({ type: 'error', text: err.message || 'Upload failed' });
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm('Are you sure you want to remove this indexed document?')) return;
    try {
      await api.deleteDocument(docId);
      loadDocuments();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    try {
      setSearching(true);
      const data = await api.searchKnowledge(searchQuery.trim(), 5);
      setSearchResults(data.results);
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  const getSourceIcon = (type: string) => {
    switch (type) {
      case 'webpage':
        return <Globe className="w-4 h-4 text-cyan-400" />;
      case 'experience':
        return <Brain className="w-4 h-4 text-indigo-400" />;
      case 'local_document':
      default:
        return <FileText className="w-4 h-4 text-emerald-400" />;
    }
  };

  return (
    <div className="space-y-6 animate-fadeIn pb-12">
      {/* Upload & Indexing Banner */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Upload Drop Area */}
        <div className="lg:col-span-6 p-6 rounded-2xl bg-nexus-900 border border-nexus-800/80 shadow-md space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-300">
              <UploadCloud className="w-5 h-5 text-cyan-400" />
              <h3 className="text-sm font-semibold">Upload Local Research Documents</h3>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">TXT, MD, PDF, JSON, CSV</span>
          </div>

          <label className="border-2 border-dashed border-nexus-800 hover:border-cyan-500/50 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition-all bg-nexus-950/60 hover:bg-nexus-950/90 group">
            <UploadCloud className="w-8 h-8 text-slate-400 group-hover:text-cyan-400 transition-colors mb-2" />
            <span className="text-xs font-semibold text-slate-200 group-hover:text-cyan-300">
              {uploading ? 'Chunking & Embedding...' : 'Choose or drag a document to index'}
            </span>
            <span className="text-[11px] text-slate-400 mt-1">
              Automatically chunks with sliding window &amp; SentenceTransformer embeddings
            </span>
            <input
              type="file"
              accept=".txt,.md,.markdown,.pdf,.json,.csv"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>

          {uploadMsg && (
            <div className={`p-3 rounded-xl text-xs flex items-center gap-2 ${
              uploadMsg.type === 'success' 
                ? 'bg-emerald-500/15 border border-emerald-500/30 text-emerald-300' 
                : 'bg-rose-500/15 border border-rose-500/30 text-rose-300'
            }`}>
              {uploadMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
              <span>{uploadMsg.text}</span>
            </div>
          )}
        </div>

        {/* Semantic Query Test Bench */}
        <div className="lg:col-span-6 p-6 rounded-2xl bg-nexus-900 border border-nexus-800/80 shadow-md space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-300">
              <Search className="w-5 h-5 text-indigo-400" />
              <h3 className="text-sm font-semibold">Semantic Vector Query Explorer</h3>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">Cosine Similarity</span>
          </div>

          <form onSubmit={handleSearch} className="space-y-3">
            <div className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Test query across stored knowledge chunks..."
                className="w-full px-4 py-2.5 rounded-xl bg-nexus-950 border border-nexus-800 text-slate-100 placeholder-slate-400 text-xs focus:outline-none focus:border-cyan-500/60"
              />
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={searching || !searchQuery.trim()}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-2 transition-all disabled:opacity-50"
              >
                {searching ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                <span>Retrieve Chunks</span>
              </button>
            </div>
          </form>

          {/* Search Result Snippets */}
          {searchResults.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-nexus-800/60 max-h-48 overflow-y-auto scrollbar-thin scrollbar-thumb-nexus-800 pr-1">
              {searchResults.map((r) => (
                <div key={r.chunk_id} className="p-2.5 rounded-lg bg-nexus-950 border border-nexus-800 text-xs space-y-1">
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-semibold text-slate-200 truncate max-w-xs">{r.title}</span>
                    <span className="px-1.5 py-0.5 rounded bg-cyan-500/10 text-cyan-300 font-mono text-[10px]">
                      {Math.round(r.relevance_score * 100)}% match
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 line-clamp-2">{r.text}</p>
                  <div className="flex items-center gap-1.5 text-[10px] text-slate-400 font-mono">
                    <span className="capitalize">{r.source_type.replace('_', ' ')}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Indexed Documents Table */}
      <div className="p-5 rounded-2xl bg-nexus-900 border border-nexus-800/80 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-white">Indexed Knowledge Documents</h3>
            <p className="text-xs text-slate-400">Embedded chunks accessible by the agent during synthesis</p>
          </div>
          <button
            onClick={loadDocuments}
            className="p-2 rounded-lg bg-nexus-800 hover:bg-nexus-700 text-slate-300 border border-nexus-700 transition-colors"
            title="Refresh document index"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {documents.length === 0 ? (
          <div className="py-12 text-center text-slate-400 border border-dashed border-nexus-800 rounded-xl space-y-2">
            <Database className="w-10 h-10 mx-auto text-slate-400" />
            <p className="text-sm font-medium">Knowledge Base is currently empty</p>
            <p className="text-xs text-slate-400">Upload a research file or execute browsing tasks to populate knowledge</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-nexus-850 text-slate-400 uppercase text-[10px] tracking-wider border-b border-nexus-800">
                <tr>
                  <th className="py-3 px-4">Document / Source</th>
                  <th className="py-3 px-4">Provenance Type</th>
                  <th className="py-3 px-4">Chunks</th>
                  <th className="py-3 px-4">Indexed At</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-nexus-800/60">
                {documents.map((doc) => (
                  <tr key={doc.doc_id} className="hover:bg-nexus-850/40 transition-colors">
                    <td className="py-3 px-4 max-w-sm truncate font-medium text-slate-200">
                      <div className="flex items-center gap-2">
                        {getSourceIcon(doc.source_type)}
                        <span className="truncate">{doc.title}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-[11px] capitalize">
                      {doc.source_type.replace('_', ' ')}
                    </td>
                    <td className="py-3 px-4 font-mono text-cyan-400 font-semibold">
                      {doc.chunk_count}
                    </td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                      {doc.created_at || 'Recent'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleDelete(doc.doc_id)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                        title="Remove from vector store"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
