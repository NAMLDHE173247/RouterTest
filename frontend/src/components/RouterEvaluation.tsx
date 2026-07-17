"use client";

import React, { useState, useEffect } from 'react';
import { runEvaluation, getEvaluationErrors, getEvaluationAnalysis, listDatasets, uploadDataset, getQwenServiceUrl } from '@/lib/api';
import { EvaluationResponse, EvaluationErrorsResponse, ErrorAnalysisResponse, DatasetListItem, DatasetUploadResponse, RouterInfo } from '@/types/router';

export default function RouterEvaluation({ routers }: { routers: RouterInfo[] }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [evaluationResponse, setEvaluationResponse] = useState<EvaluationResponse | null>(null);
  const [evaluationErrors, setEvaluationErrors] = useState<EvaluationErrorsResponse | null>(null);
  const [evaluationAnalysis, setEvaluationAnalysis] = useState<ErrorAnalysisResponse | null>(null);

  const [datasets, setDatasets] = useState<DatasetListItem[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('');
  const [uploadingDataset, setUploadingDataset] = useState<boolean>(false);
  const [uploadResult, setUploadResult] = useState<DatasetUploadResponse | null>(null);

  const [selectedRouterIds, setSelectedRouterIds] = useState<string[]>([]);
  const [sampleLimit, setSampleLimit] = useState<string>('20');

  const [evalFilterRouter, setEvalFilterRouter] = useState<string>('all');
  const [evalFilterType, setEvalFilterType] = useState<string>('all');
  
  // Pagination for errors list
  const [currentPage, setCurrentPage] = useState<number>(1);
  const errorsPerPage = 20;

  useEffect(() => {
    async function init() {
      try {
        const dsets = await listDatasets();
        setDatasets(dsets);
        if (dsets.length > 0) setSelectedDatasetId(dsets[0].dataset_id);
      } catch (e: any) {
        console.error('Failed to load datasets', e);
      }
    }
    init();
  }, []);

  const toggleRouter = (id: string) => {
    setSelectedRouterIds(prev => 
      prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]
    );
  };

  const handleRun = async () => {
    if (selectedRouterIds.length === 0) {
      setError('Vui lòng chọn ít nhất 1 Router để đánh giá');
      return;
    }

    if (selectedRouterIds.includes('qwen_v0')) {
       try {
         const config = await getQwenServiceUrl();
         if (!config.url) {
            setError('Qwen GPU Service URL is not configured. Please configure it in the settings tab.');
            return;
         }
       } catch (e) {
         // Fallback to let backend handle connection errors gracefully
       }
    }

    setLoading(true);
    setError(null);
    setEvaluationResponse(null);
    setEvaluationErrors(null);
    setEvaluationAnalysis(null);
    setCurrentPage(1);
    
    try {
      const limitVal = sampleLimit === 'full' ? undefined : parseInt(sampleLimit);
      const resEval = await runEvaluation(selectedRouterIds, selectedDatasetId, limitVal);
      setEvaluationResponse(resEval);
      
      if (resEval.run_id) {
        const [errorsRes, analysisRes] = await Promise.all([
          getEvaluationErrors(resEval.run_id).catch(() => null),
          getEvaluationAnalysis(resEval.run_id).catch(() => null)
        ]);
        if (errorsRes) setEvaluationErrors(errorsRes);
        if (analysisRes) setEvaluationAnalysis(analysisRes);
      }
    } catch (e: any) {
      setError(e.message || 'Có lỗi xảy ra khi gọi API');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    
    setUploadingDataset(true);
    setUploadResult(null);
    try {
      const res = await uploadDataset(file);
      setUploadResult(res);
      const dsets = await listDatasets();
      setDatasets(dsets);
      if (res.dataset_id) {
        setSelectedDatasetId(res.dataset_id);
      }
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploadingDataset(false);
      e.target.value = '';
    }
  };

  const availableRouters = routers.length > 0 ? routers : [
    { id: 'rule_v0', name: 'Rule-based Router V0', status: 'ready' },
    { id: 'rule_v1', name: 'Rule-based Router V1', status: 'ready' },
    { id: 'rule_v2', name: 'Rule-based Router V2', status: 'ready' },
    { id: 'rule_v3', name: 'Rule-based Router V3 (Phase 0)', status: 'ready' },
    { id: 'qwen_v0', name: 'Qwen Router V0 (GPU Service)', status: 'ready' },
    { id: 'hybrid', name: 'Hybrid Router', status: 'ready' } // Handled manually below
  ];

  const hasQwen = selectedRouterIds.includes('qwen_v0');
  const isFullQwen = hasQwen && sampleLimit === 'full';

  const renderAnalysisMode = () => {
    if (!evaluationAnalysis) return null;
    const an = evaluationAnalysis;
    const rids = Object.keys(an.total_errors_by_router);
    if (rids.length === 0) return null;
    
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-6 animate-in fade-in">
        <h2 className="text-xl font-bold mb-4 border-b pb-2 text-gray-800">Error Analysis</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Errors by Case Type</h3>
            <table className="w-full text-sm text-left border">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-1 border-b">Case Type</th>
                  <th className="px-2 py-1 border-b">Total</th>
                  {rids.map(r => <th key={r} className="px-2 py-1 border-b text-xs">{r}</th>)}
                </tr>
              </thead>
              <tbody>
                {Object.entries(an.errors_by_case_type).map(([ctype, total]) => (
                  <tr key={ctype} className="border-b">
                    <td className="px-2 py-1 font-medium">{ctype}</td>
                    <td className="px-2 py-1">{total as number}</td>
                    {rids.map(r => <td key={r} className="px-2 py-1">{an.errors_by_router_and_case_type[r]?.[ctype] || 0}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Clarification False Positive / Negative</h3>
            <table className="w-full text-sm text-left border">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-1 border-b">Router</th>
                  <th className="px-2 py-1 border-b text-red-600">False Positive</th>
                  <th className="px-2 py-1 border-b text-blue-600">False Negative</th>
                </tr>
              </thead>
              <tbody>
                {rids.map(r => (
                  <tr key={r} className="border-b">
                    <td className="px-2 py-1 font-medium">{r}</td>
                    <td className="px-2 py-1">{an.clarification_errors[r]?.false_positive || 0}</td>
                    <td className="px-2 py-1">{an.clarification_errors[r]?.false_negative || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Top Intent Confusion</h3>
            <div className="max-h-60 overflow-y-auto border rounded">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-2 py-1 border-b">Router</th>
                    <th className="px-2 py-1 border-b">Gold ➔ Predicted</th>
                    <th className="px-2 py-1 border-b">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {an.intent_confusion.slice(0, 15).map((conf, idx) => (
                    <tr key={idx} className="border-b">
                      <td className="px-2 py-1">{conf.router_id}</td>
                      <td className="px-2 py-1 font-medium text-xs">
                        <span className="text-green-600">{conf.gold}</span> ➔ <span className="text-red-600">{conf.predicted}</span>
                      </td>
                      <td className="px-2 py-1">{conf.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Top Subject Confusion</h3>
            <div className="max-h-60 overflow-y-auto border rounded">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-2 py-1 border-b">Router</th>
                    <th className="px-2 py-1 border-b">Gold ➔ Predicted</th>
                    <th className="px-2 py-1 border-b">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {an.subject_confusion.slice(0, 15).map((conf, idx) => (
                    <tr key={idx} className="border-b">
                      <td className="px-2 py-1">{conf.router_id}</td>
                      <td className="px-2 py-1 font-medium text-xs">
                        <span className="text-green-600">{conf.gold}</span> ➔ <span className="text-red-600">{conf.predicted}</span>
                      </td>
                      <td className="px-2 py-1">{conf.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderMetrics = () => {
    if (!evaluationResponse) return null;
    const m = evaluationResponse.metrics;
    const rids = Object.keys(m);
    if (rids.length === 0) return null;
    
    // Helpers to find best metrics
    const getBestMax = (key: keyof typeof m[string]) => {
      let max = -1;
      for (const rid of rids) if ((m[rid][key] as number) > max) max = m[rid][key] as number;
      return max;
    };
    
    const getBestMin = (key: keyof typeof m[string]) => {
      let min = Infinity;
      for (const rid of rids) if ((m[rid][key] as number) < min) min = m[rid][key] as number;
      return min;
    };
    
    const bestPS = getBestMax('primary_subject_accuracy');
    const bestIntent = getBestMax('intent_accuracy');
    const bestTarget = getBestMax('target_slm_accuracy');
    const bestNC = getBestMax('need_clarification_accuracy');
    const bestEM = getBestMax('exact_match_accuracy');
    
    const bestTotalErrors = getBestMin('total_errors');
    const bestLatency = getBestMin('average_latency_ms');

    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-6 animate-in fade-in">
        <h2 className="text-xl font-bold mb-4 border-b pb-2 text-gray-800">Metrics Dashboard (Run: {evaluationResponse.run_id})</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-2 font-medium text-gray-600">Metric</th>
                {rids.map(rid => <th key={rid} className="px-4 py-2 font-medium text-gray-600">{rid}</th>)}
              </tr>
            </thead>
            <tbody className="divide-y">
              <tr>
                <td className="px-4 py-2 text-gray-700">Total Samples</td>
                {rids.map(rid => <td key={rid} className="px-4 py-2">{m[rid].total_samples}</td>)}
              </tr>
              <tr>
                <td className="px-4 py-2 text-gray-700">Primary Subject Accuracy</td>
                {rids.map(rid => (
                  <td key={rid} className={`px-4 py-2 ${m[rid].primary_subject_accuracy === bestPS ? 'text-green-600 font-bold bg-green-50' : ''}`}>
                    {(m[rid].primary_subject_accuracy * 100).toFixed(1)}%
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-4 py-2 text-gray-700">Intent Accuracy</td>
                {rids.map(rid => (
                  <td key={rid} className={`px-4 py-2 ${m[rid].intent_accuracy === bestIntent ? 'text-green-600 font-bold bg-green-50' : ''}`}>
                    {(m[rid].intent_accuracy * 100).toFixed(1)}%
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-4 py-2 text-gray-700">Target SLM Accuracy</td>
                {rids.map(rid => (
                  <td key={rid} className={`px-4 py-2 ${m[rid].target_slm_accuracy === bestTarget ? 'text-green-600 font-bold bg-green-50' : ''}`}>
                    {(m[rid].target_slm_accuracy * 100).toFixed(1)}%
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-4 py-2 text-gray-700">Need Clarification Acc</td>
                {rids.map(rid => (
                  <td key={rid} className={`px-4 py-2 ${m[rid].need_clarification_accuracy === bestNC ? 'text-green-600 font-bold bg-green-50' : ''}`}>
                    {(m[rid].need_clarification_accuracy * 100).toFixed(1)}%
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-4 py-2 text-gray-700">Exact Match (All Fields)</td>
                {rids.map(rid => (
                  <td key={rid} className={`px-4 py-2 ${m[rid].exact_match_accuracy === bestEM ? 'text-green-600 font-bold bg-green-50' : ''}`}>
                    {(m[rid].exact_match_accuracy * 100).toFixed(1)}%
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-4 py-2 text-gray-700">Total Errors</td>
                {rids.map(rid => (
                  <td key={rid} className={`px-4 py-2 ${m[rid].total_errors === bestTotalErrors ? 'text-green-600 font-bold bg-green-50' : 'text-red-600'}`}>
                    {m[rid].total_errors}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="px-4 py-2 text-gray-700">Average Latency (ms)</td>
                {rids.map(rid => (
                  <td key={rid} className={`px-4 py-2 ${m[rid].average_latency_ms === bestLatency ? 'text-green-600 font-bold bg-green-50' : ''}`}>
                    {m[rid].average_latency_ms.toFixed(2)} ms
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderErrorsList = () => {
    if (!evaluationErrors) return null;
    const rids = Object.keys(evaluationResponse?.metrics || {});
    
    const filteredErrors = evaluationErrors.errors.filter(err => {
      if (evalFilterRouter !== 'all' && err.router_id !== evalFilterRouter) return false;
      if (evalFilterType !== 'all' && err.case_type !== evalFilterType) return false;
      return true;
    });

    const uniqueCaseTypes = Array.from(new Set(evaluationErrors.errors.map(e => e.case_type) || []));

    // Pagination
    const totalPages = Math.ceil(filteredErrors.length / errorsPerPage);
    const paginatedErrors = filteredErrors.slice((currentPage - 1) * errorsPerPage, currentPage * errorsPerPage);

    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-6 animate-in fade-in">
        <div className="flex justify-between items-center border-b pb-2 mb-4">
          <h2 className="text-xl font-bold text-gray-800">Errors List ({filteredErrors.length})</h2>
          <div className="flex gap-2">
            <select 
              className="border text-sm p-1 rounded outline-none focus:ring-1 focus:ring-blue-500"
              value={evalFilterRouter}
              onChange={e => { setEvalFilterRouter(e.target.value); setCurrentPage(1); }}
            >
              <option value="all">All Routers</option>
              {rids.map(r => <option key={r} value={r}>{r}</option>)}
            </select>
            <select 
              className="border text-sm p-1 rounded outline-none focus:ring-1 focus:ring-blue-500"
              value={evalFilterType}
              onChange={e => { setEvalFilterType(e.target.value); setCurrentPage(1); }}
            >
              <option value="all">All Case Types</option>
              {uniqueCaseTypes.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>

        <div className="space-y-4">
          {paginatedErrors.map((err, idx) => (
            <div key={idx} className="border border-red-200 bg-red-50 p-4 rounded text-sm transition-all hover:shadow-md">
              <div className="flex justify-between mb-2">
                <span className="font-bold text-red-800">{err.id} - {err.router_id}</span>
                <span className="text-xs bg-red-200 text-red-800 px-2 py-0.5 rounded">{err.case_type}</span>
              </div>
              <p className="mb-2 text-gray-800"><span className="font-semibold">Q:</span> {err.question}</p>
              
              <div className="grid grid-cols-2 gap-4 mt-3">
                <div className="bg-white p-2 rounded border">
                  <div className="text-xs font-bold text-gray-500 mb-1">GOLD</div>
                  {err.wrong_fields.map(f => (
                    <div key={f} className="text-xs mb-1">
                      <span className="font-semibold">{f}:</span> {String(err.gold[f])}
                    </div>
                  ))}
                </div>
                <div className="bg-white p-2 rounded border border-red-300">
                  <div className="text-xs font-bold text-red-500 mb-1">PREDICTION</div>
                  {err.wrong_fields.map(f => (
                    <div key={f} className="text-xs mb-1 text-red-700">
                      <span className="font-semibold">{f}:</span> {String(err.prediction[f])}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
          {filteredErrors.length === 0 && <div className="text-gray-500 italic text-center p-4">No errors found for this filter.</div>}
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="flex justify-center items-center gap-4 mt-6">
            <button 
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50"
            >
              Previous
            </button>
            <span className="text-sm font-medium text-gray-700">Page {currentPage} of {totalPages}</span>
            <button 
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50"
            >
              Next
            </button>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6 pb-20">
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h2 className="text-xl font-bold mb-4 text-gray-800">Dataset Settings</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-6">
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Select Dataset</h3>
            <select 
              value={selectedDatasetId}
              onChange={e => setSelectedDatasetId(e.target.value)}
              className="w-full border border-gray-300 rounded p-2 bg-white focus:ring-2 focus:ring-blue-500 outline-none mb-2"
            >
              {datasets.map(d => (
                <option key={d.dataset_id} value={d.dataset_id}>
                  {d.name} ({d.total_samples} samples)
                </option>
              ))}
            </select>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Upload Custom Dataset</h3>
            <label className={`flex items-center justify-center border border-gray-300 rounded px-4 py-2 cursor-pointer transition-colors text-sm ${uploadingDataset ? 'bg-gray-100 text-gray-400' : 'bg-white hover:bg-gray-50 text-gray-700'}`}>
              {uploadingDataset ? 'Uploading...' : 'Choose .jsonl or .json File'}
              <input type="file" accept=".jsonl,.json" className="hidden" onChange={handleUpload} disabled={uploadingDataset} />
            </label>
            {uploadResult && (
              <p className={`text-xs mt-2 ${uploadResult.status === 'valid' ? 'text-green-600' : 'text-red-600'}`}>
                {uploadResult.status === 'valid' ? `Success: ${uploadResult.valid_samples} samples.` : 'Upload failed.'}
              </p>
            )}
          </div>
        </div>

        <div className="border-t pt-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Evaluation Configuration</h3>
          
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600 mb-2 font-medium">Select Routers:</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {availableRouters.map(r => {
                  const isDisabled = (r.status && r.status !== 'ready') || (r as any).enabled === false || r.id === 'hybrid';
                  return (
                    <label 
                      key={r.id} 
                      className={`flex items-start gap-2 p-3 rounded border cursor-pointer transition-colors ${isDisabled ? 'bg-gray-50 opacity-60 cursor-not-allowed' : selectedRouterIds.includes(r.id) ? 'bg-blue-50 border-blue-200' : 'bg-white hover:bg-gray-50'}`}
                    >
                      <input 
                        type="checkbox" 
                        className="mt-1 w-4 h-4 text-blue-600 focus:ring-blue-500 rounded border-gray-300 disabled:opacity-50"
                        checked={selectedRouterIds.includes(r.id)}
                        onChange={() => toggleRouter(r.id)}
                        disabled={isDisabled}
                      />
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-gray-800">{r.name}</span>
                        {r.id === 'hybrid' && <span className="text-xs text-amber-600 font-semibold">Coming soon</span>}
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>
            
            <div className="pt-2">
              <p className="text-sm text-gray-600 mb-2 font-medium">Sample Limit:</p>
              <div className="flex gap-4">
                {['20', '50', '100', 'full'].map(limit => (
                  <label key={limit} className="flex items-center gap-1 cursor-pointer">
                    <input 
                      type="radio" 
                      name="sampleLimit" 
                      value={limit} 
                      checked={sampleLimit === limit}
                      onChange={(e) => setSampleLimit(e.target.value)}
                      className="text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm uppercase">{limit}</span>
                  </label>
                ))}
              </div>
              {isFullQwen && (
                <div className="mt-3 p-3 bg-amber-50 text-amber-800 text-sm rounded border border-amber-200 font-medium">
                  ⚠️ Cảnh báo: Việc chạy đánh giá toàn bộ Dataset bằng Qwen V0 (GPU Service) sẽ tốn rất nhiều thời gian. Hãy thử nghiệm với 20-50 samples trước.
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="mt-6 flex items-center gap-4">
          <button 
            onClick={handleRun} 
            disabled={loading || selectedRouterIds.length === 0} 
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-semibold px-6 py-2.5 rounded-md shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Evaluating...' : 'Run Evaluation'}
          </button>
          {error && <span className="text-red-600 text-sm font-medium">{error}</span>}
        </div>
      </div>

      {loading && (
        <div className="bg-white p-10 rounded-lg shadow-sm border border-gray-200 text-center animate-in fade-in">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600 font-medium">Đang chạy Evaluation... Quá trình này có thể mất thời gian tuỳ thuộc vào Model.</p>
        </div>
      )}

      {!loading && renderMetrics()}
      {!loading && renderAnalysisMode()}
      {!loading && renderErrorsList()}

    </div>
  );
}
