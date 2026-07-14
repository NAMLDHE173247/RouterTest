"use client";

import { useEffect, useState } from 'react';
import { getHealth, getRouters, routeQuestion, compareRouters, runEvaluation, getEvaluationErrors, getEvaluationAnalysis, listDatasets, uploadDataset } from '@/lib/api';
import { RouterInfo, RouteResponse, CompareResponse, EvaluationResponse, EvaluationErrorsResponse, ErrorAnalysisResponse, DatasetListItem, DatasetUploadResponse } from '@/types/router';

export default function Home() {
  const [healthStatus, setHealthStatus] = useState<string>('checking...');
  const [routers, setRouters] = useState<RouterInfo[]>([]);
  
  // Modes
  const [mode, setMode] = useState<'single' | 'compare' | 'evaluation'>('single');
  
  // Inputs
  const [selectedRouter, setSelectedRouter] = useState<string>('rule_v2');
  const [question, setQuestion] = useState<string>('');
  const [history, setHistory] = useState<string>('');
  
  // States
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // Results
  const [singleResponse, setSingleResponse] = useState<RouteResponse | null>(null);
  const [compareResponse, setCompareResponse] = useState<CompareResponse | null>(null);
  const [evaluationResponse, setEvaluationResponse] = useState<EvaluationResponse | null>(null);
  const [evaluationErrors, setEvaluationErrors] = useState<EvaluationErrorsResponse | null>(null);
  const [evaluationAnalysis, setEvaluationAnalysis] = useState<ErrorAnalysisResponse | null>(null);

  // Datasets
  const [datasets, setDatasets] = useState<DatasetListItem[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('default_v2_test_router');
  const [uploadingDataset, setUploadingDataset] = useState<boolean>(false);
  const [uploadResult, setUploadResult] = useState<DatasetUploadResponse | null>(null);

  // Filters for Eval
  const [evalFilterRouter, setEvalFilterRouter] = useState<string>('all');
  const [evalFilterType, setEvalFilterType] = useState<string>('all');

  useEffect(() => {
    async function init() {
      try {
        const health = await getHealth();
        setHealthStatus(health.status);
      } catch (e: any) {
        setHealthStatus('offline');
        console.error(e);
      }

      try {
        const routersList = await getRouters();
        setRouters(routersList);
        if (routersList.length > 0 && !routersList.find(r => r.id === selectedRouter)) {
          setSelectedRouter(routersList[0].id);
        }
      } catch (e: any) {
        console.error('Failed to load routers', e);
      }
      
      try {
        const dsets = await listDatasets();
        setDatasets(dsets);
      } catch (e: any) {
        console.error('Failed to load datasets', e);
      }
    }
    init();
  }, []);

  const handleRun = async () => {
    if (mode !== 'evaluation' && !question.trim()) {
      setError('Vui lòng nhập câu hỏi');
      return;
    }
    
    setLoading(true);
    setError(null);
    setSingleResponse(null);
    setCompareResponse(null);
    setEvaluationResponse(null);
    setEvaluationErrors(null);
    setEvaluationAnalysis(null);
    
    const historyArray = history.split('\n').map(s => s.trim()).filter(s => s.length > 0);
    
    try {
      if (mode === 'single') {
        const res = await routeQuestion({
          router_id: selectedRouter,
          question: question,
          history: historyArray
        });
        setSingleResponse(res);
      } else if (mode === 'compare') {
        const res = await compareRouters({
          question: question,
          history: historyArray,
          router_ids: ["rule_v0", "rule_v1", "rule_v2"]
        });
        setCompareResponse(res);
      } else if (mode === 'evaluation') {
        const resEval = await runEvaluation(["rule_v0", "rule_v1", "rule_v2"], selectedDatasetId);
        setEvaluationResponse(resEval);
        
        if (resEval.run_id) {
          const [errorsRes, analysisRes] = await Promise.all([
            getEvaluationErrors(resEval.run_id).catch(() => null),
            getEvaluationAnalysis(resEval.run_id).catch(() => null)
          ]);
          if (errorsRes) setEvaluationErrors(errorsRes);
          if (analysisRes) setEvaluationAnalysis(analysisRes);
        }
      }
    } catch (e: any) {
      setError(e.message || 'Có lỗi xảy ra khi gọi API');
    } finally {
      setLoading(false);
    }
  };

  const setExample = (type: string) => {
    if (type === 'multi-turn') {
      setHistory("Em đang học phương trình bậc hai.\nEm nhớ công thức delta là b^2 - 4ac nhưng chưa chắc cách xét nghiệm.");
      setQuestion("Vậy nếu delta bằng 0 thì phương trình có mấy nghiệm?");
    } else if (type === 'interdisciplinary') {
      setHistory("");
      setQuestion("Làm sao để ứng dụng tích phân vào việc tính công sinh ra bởi lực hấp dẫn?");
    } else if (type === 'ambiguous') {
      setHistory("");
      setQuestion("Bài này giải sao ạ?");
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
      // Refresh datasets list
      const dsets = await listDatasets();
      setDatasets(dsets);
      if (res.dataset_id) {
        setSelectedDatasetId(res.dataset_id);
      }
    } catch (err: any) {
      let parsedMessage = err.message;
      try {
        const parsed = JSON.parse(err.message);
        if (parsed.message) {
          parsedMessage = parsed.message;
          setUploadResult(parsed);
        }
      } catch (e) {}
      setError(parsedMessage || 'Upload failed');
    } finally {
      setUploadingDataset(false);
      // clear input
      e.target.value = '';
    }
  };

  const getDiffFields = () => {
    if (!compareResponse?.comparisons || compareResponse.comparisons.length < 2) return new Set<string>();
    const fields = ['primary_subject', 'intent', 'target_slm', 'confidence', 'need_clarification'];
    const diffs = new Set<string>();
    const responses = compareResponse.comparisons.map(c => c.response?.decision).filter(Boolean);
    if (responses.length < 2) return diffs;

    for (const field of fields) {
      // @ts-ignore
      const values = responses.map(r => String(r[field]));
      const uniqueValues = new Set(values);
      if (uniqueValues.size > 1) {
        diffs.add(field);
      }
    }
    return diffs;
  };

  const diffFields = mode === 'compare' ? getDiffFields() : new Set<string>();

  const renderSingleResult = (res: RouteResponse | null) => {
    if (!res) return null;
    const getBadgeClass = (field: string, defaultClass: string) => {
      if (diffFields.has(field)) return 'bg-yellow-100 text-yellow-800 border-yellow-300 ring-2 ring-yellow-300 font-bold';
      return defaultClass;
    };

    return (
      <div className="flex-1 flex flex-col space-y-4">
        <div className="grid grid-cols-2 gap-y-3 gap-x-3 text-sm">
          <div>
            <div className="text-gray-500 text-[10px] uppercase tracking-wider font-semibold">Primary Subject</div>
            <div className={`py-1 px-2 rounded inline-block mt-1 border transition-colors ${getBadgeClass('primary_subject', 'text-blue-700 bg-blue-50 border-blue-100 font-medium')}`}>
              {res.decision.primary_subject}
            </div>
          </div>
          <div>
            <div className="text-gray-500 text-[10px] uppercase tracking-wider font-semibold">Intent</div>
            <div className={`py-1 px-2 rounded inline-block mt-1 border transition-colors ${getBadgeClass('intent', 'text-purple-700 bg-purple-50 border-purple-100 font-medium')}`}>
              {res.decision.intent}
            </div>
          </div>
          <div>
            <div className="text-gray-500 text-[10px] uppercase tracking-wider font-semibold">Target SLM</div>
            <div className={`py-1 px-2 rounded inline-block mt-1 border transition-colors ${getBadgeClass('target_slm', 'text-amber-700 bg-amber-50 border-amber-100 font-medium')}`}>
              {res.decision.target_slm}
            </div>
          </div>
          <div>
            <div className="text-gray-500 text-[10px] uppercase tracking-wider font-semibold">Confidence</div>
            <div className={`py-1 px-2 rounded inline-block mt-1 border transition-colors ${getBadgeClass('confidence', 'text-green-700 bg-green-50 border-green-100 font-medium')}`}>
              {(res.decision.confidence * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-gray-500 text-[10px] uppercase tracking-wider font-semibold">Need Clarification</div>
            <div className={`mt-1 text-sm ${diffFields.has('need_clarification') ? 'text-yellow-700 font-bold' : 'text-gray-900 font-medium'}`}>
              {res.decision.need_clarification ? 'Yes' : 'No'}
            </div>
          </div>
          <div>
            <div className="text-gray-500 text-[10px] uppercase tracking-wider font-semibold">Latency</div>
            <div className="font-medium text-gray-900 mt-1 text-sm">
              {res.runtime.latency_ms.toFixed(2)} ms
            </div>
          </div>
          <div className="col-span-2">
            <div className="text-gray-500 text-[10px] uppercase tracking-wider font-semibold">Secondary Subjects</div>
            <div className="font-medium text-gray-700 mt-1 text-sm">
              {res.decision.secondary_subjects.length > 0 
                ? res.decision.secondary_subjects.join(', ') 
                : 'None'}
            </div>
          </div>
          <div className="col-span-2">
            <div className="text-gray-500 text-[10px] uppercase tracking-wider font-semibold">Reason</div>
            <div className="font-medium text-gray-700 mt-1 bg-gray-50 p-2 rounded border border-gray-200 text-xs">
              {res.decision.reason}
            </div>
          </div>
        </div>
        <div className="mt-auto pt-4 border-t">
          <details className="group cursor-pointer">
            <summary className="text-[10px] uppercase tracking-wider font-semibold text-gray-500 mb-2 list-none flex items-center hover:text-gray-700">
              <span className="mr-2 text-[8px] transition-transform group-open:rotate-90">▶</span>
              Raw JSON
            </summary>
            <pre className="bg-gray-800 text-green-400 p-2 rounded text-[10px] overflow-x-auto shadow-inner border border-gray-700 max-h-32 mt-2">
              {JSON.stringify(res, null, 2)}
            </pre>
          </details>
        </div>
      </div>
    );
  };

  const renderAnalysisMode = () => {
    if (!evaluationAnalysis) return null;
    const an = evaluationAnalysis;
    const rids = ['rule_v0', 'rule_v1', 'rule_v2'];
    
    return (
      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mt-6">
        <h2 className="text-xl font-semibold mb-4 border-b pb-2 text-gray-800">Error Analysis Lite</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Total Errors By Router & Field */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Errors by Field</h3>
            <table className="w-full text-sm text-left border">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-2 py-1 border-b">Field</th>
                  <th className="px-2 py-1 border-b">Total</th>
                  {rids.map(r => <th key={r} className="px-2 py-1 border-b text-xs">{r}</th>)}
                </tr>
              </thead>
              <tbody>
                {Object.entries(an.errors_by_field).map(([field, total]) => (
                  <tr key={field} className="border-b">
                    <td className="px-2 py-1 font-medium">{field}</td>
                    <td className="px-2 py-1">{total as number}</td>
                    {rids.map(r => <td key={r} className="px-2 py-1">{an.errors_by_router_and_field[r]?.[field] || 0}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Errors by Case Type */}
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

          {/* Clarification FP / FN */}
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

          {/* Top Intent Confusion */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Top Intent Confusion</h3>
            <div className="max-h-40 overflow-y-auto border rounded">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-2 py-1 border-b">Router</th>
                    <th className="px-2 py-1 border-b">Gold ➔ Predicted</th>
                    <th className="px-2 py-1 border-b">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {an.intent_confusion.slice(0, 10).map((conf, idx) => (
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
          
          {/* Top Subject Confusion */}
          <div className="col-span-1 md:col-span-2">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Top Subject Confusion</h3>
            <div className="max-h-40 overflow-y-auto border rounded">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    <th className="px-2 py-1 border-b">Router</th>
                    <th className="px-2 py-1 border-b">Gold ➔ Predicted</th>
                    <th className="px-2 py-1 border-b">Count</th>
                  </tr>
                </thead>
                <tbody>
                  {an.subject_confusion.slice(0, 10).map((conf, idx) => (
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

  const renderEvaluationMode = () => {
    if (!evaluationResponse) {
      return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 h-full flex items-center justify-center text-gray-400 italic">
          {loading ? 'Evaluating dataset (this may take a few seconds)...' : 'Run evaluation to see metrics over the dataset'}
        </div>
      );
    }

    const m = evaluationResponse.metrics;
    const rids = Object.keys(m);
    
    // Helper to find best metric
    const getBest = (key: keyof typeof m[string]) => {
      let max = -1;
      for (const rid of rids) {
        if (m[rid][key] > max) max = m[rid][key] as number;
      }
      return max;
    };
    
    const bestPS = getBest('primary_subject_accuracy');
    const bestIntent = getBest('intent_accuracy');
    const bestTarget = getBest('target_slm_accuracy');
    const bestEM = getBest('exact_match_accuracy');

    const filteredErrors = evaluationErrors?.errors.filter(err => {
      if (evalFilterRouter !== 'all' && err.router_id !== evalFilterRouter) return false;
      if (evalFilterType !== 'all' && err.case_type !== evalFilterType) return false;
      return true;
    }) || [];

    const uniqueCaseTypes = Array.from(new Set(evaluationErrors?.errors.map(e => e.case_type) || []));

    return (
      <div className="flex flex-col space-y-6">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-xl font-semibold mb-4 border-b pb-2 text-gray-800">Metrics (Run: {evaluationResponse.run_id})</h2>
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
                  <td className="px-4 py-2 text-gray-700">Primary Subject Acc</td>
                  {rids.map(rid => (
                    <td key={rid} className={`px-4 py-2 ${m[rid].primary_subject_accuracy === bestPS ? 'text-green-600 font-bold bg-green-50' : ''}`}>
                      {(m[rid].primary_subject_accuracy * 100).toFixed(1)}%
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="px-4 py-2 text-gray-700">Intent Acc</td>
                  {rids.map(rid => (
                    <td key={rid} className={`px-4 py-2 ${m[rid].intent_accuracy === bestIntent ? 'text-green-600 font-bold bg-green-50' : ''}`}>
                      {(m[rid].intent_accuracy * 100).toFixed(1)}%
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="px-4 py-2 text-gray-700">Target SLM Acc</td>
                  {rids.map(rid => (
                    <td key={rid} className={`px-4 py-2 ${m[rid].target_slm_accuracy === bestTarget ? 'text-green-600 font-bold bg-green-50' : ''}`}>
                      {(m[rid].target_slm_accuracy * 100).toFixed(1)}%
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="px-4 py-2 text-gray-700">Exact Match (4 fields)</td>
                  {rids.map(rid => (
                    <td key={rid} className={`px-4 py-2 ${m[rid].exact_match_accuracy === bestEM ? 'text-green-600 font-bold bg-green-50' : ''}`}>
                      {(m[rid].exact_match_accuracy * 100).toFixed(1)}%
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="px-4 py-2 text-gray-700">Average Latency</td>
                  {rids.map(rid => <td key={rid} className="px-4 py-2">{m[rid].average_latency_ms.toFixed(2)} ms</td>)}
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* --- ERROR ANALYSIS MODULE --- */}
        {renderAnalysisMode()}

        {evaluationErrors && (
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="flex justify-between items-center border-b pb-2 mb-4">
              <h2 className="text-xl font-semibold text-gray-800">Errors List ({filteredErrors.length})</h2>
              <div className="flex gap-2">
                <select 
                  className="border text-sm p-1 rounded outline-none focus:ring-1 focus:ring-blue-500"
                  value={evalFilterRouter}
                  onChange={e => setEvalFilterRouter(e.target.value)}
                >
                  <option value="all">All Routers</option>
                  {rids.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
                <select 
                  className="border text-sm p-1 rounded outline-none focus:ring-1 focus:ring-blue-500"
                  value={evalFilterType}
                  onChange={e => setEvalFilterType(e.target.value)}
                >
                  <option value="all">All Case Types</option>
                  {uniqueCaseTypes.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>

            <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
              {filteredErrors.map((err, idx) => (
                <div key={idx} className="border border-red-200 bg-red-50 p-4 rounded text-sm">
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

                  <details className="mt-3 group cursor-pointer">
                    <summary className="text-[10px] uppercase tracking-wider font-semibold text-gray-500 list-none flex items-center hover:text-gray-700">
                      <span className="mr-2 text-[8px] transition-transform group-open:rotate-90">▶</span>
                      Raw Error Item
                    </summary>
                    <pre className="bg-gray-800 text-gray-200 p-2 rounded text-[10px] overflow-x-auto mt-2">
                      {JSON.stringify(err, null, 2)}
                    </pre>
                  </details>
                </div>
              ))}
              {filteredErrors.length === 0 && <div className="text-gray-500 italic">No errors found for this filter.</div>}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans p-4 sm:p-8">
      <header className="mb-8 border-b pb-4">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-2 text-blue-600">Router Playground</h1>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-1">
                Backend Status: 
                <span className={`font-semibold ml-1 ${healthStatus === 'ok' ? 'text-green-600' : 'text-red-600'}`}>
                  {healthStatus.toUpperCase()}
                </span>
              </div>
            </div>
          </div>
          <div className="flex bg-gray-200 p-1 rounded-lg">
            <button 
              onClick={() => { setMode('single'); setCompareResponse(null); setEvaluationResponse(null); }}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${mode === 'single' ? 'bg-white shadow text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
            >
              Single Router
            </button>
            <button 
              onClick={() => { setMode('compare'); setSingleResponse(null); setEvaluationResponse(null); }}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${mode === 'compare' ? 'bg-white shadow text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
            >
              Compare Routers
            </button>
            <button 
              onClick={() => { setMode('evaluation'); setSingleResponse(null); setCompareResponse(null); }}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${mode === 'evaluation' ? 'bg-white shadow text-blue-600' : 'text-gray-600 hover:text-gray-900'}`}
            >
              Evaluation
            </button>
          </div>
        </div>
      </header>

      <main className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {mode !== 'evaluation' && (
          <div className="xl:col-span-4 bg-white p-6 rounded-lg shadow-sm border border-gray-200 h-fit">
            <h2 className="text-xl font-semibold mb-4 border-b pb-2 text-gray-800">Input</h2>
            
            {mode === 'single' && (
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">Select Router</label>
                <select 
                  value={selectedRouter}
                  onChange={e => setSelectedRouter(e.target.value)}
                  className="w-full border border-gray-300 rounded p-2 bg-gray-50 focus:ring-2 focus:ring-blue-500 outline-none"
                >
                  {routers.map(r => (
                    <option key={r.id} value={r.id}>{r.name}</option>
                  ))}
                  {routers.length === 0 && <option value="rule_v2">Rule-based Router V2</option>}
                </select>
              </div>
            )}

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Current Question</label>
              <p className="text-xs text-gray-500 mb-2">Chỉ nhập câu hỏi hiện tại của học sinh, không nhập toàn bộ đoạn hội thoại vào đây.</p>
              <textarea 
                value={question}
                onChange={e => setQuestion(e.target.value)}
                placeholder="e.g. Một vật rơi tự do trong 5 giây, tính vận tốc cuối cùng."
                className="w-full border border-gray-300 rounded p-2 h-24 bg-gray-50 focus:ring-2 focus:ring-blue-500 outline-none resize-y"
              />
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">History (Optional)</label>
              <p className="text-xs text-gray-500 mb-2">Mỗi dòng là một lượt hội thoại trước đó. Dùng cho các câu hỏi multi-turn.</p>
              <textarea 
                value={history}
                onChange={e => setHistory(e.target.value)}
                placeholder="e.g. Em đang làm bài rơi tự do.&#10;Dùng công thức s = 1/2gt^2."
                className="w-full border border-gray-300 rounded p-2 h-24 bg-gray-50 focus:ring-2 focus:ring-blue-500 outline-none text-sm resize-y"
              />
            </div>

            <button 
              onClick={handleRun}
              disabled={loading}
              className={`w-full py-2 px-4 rounded font-medium text-white transition-colors mb-6 ${loading ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}
            >
              {loading ? 'Processing...' : (mode === 'single' ? 'Run Router' : 'Compare Routers')}
            </button>

            <div className="border-t pt-4">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Quick Examples</p>
              <div className="flex flex-wrap gap-2">
                <button 
                  onClick={() => setExample('interdisciplinary')}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 py-1.5 px-3 rounded border border-gray-200 transition-colors"
                >
                  Example: Interdisciplinary
                </button>
                <button 
                  onClick={() => setExample('multi-turn')}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 py-1.5 px-3 rounded border border-gray-200 transition-colors"
                >
                  Example: Multi-turn
                </button>
                <button 
                  onClick={() => setExample('ambiguous')}
                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 py-1.5 px-3 rounded border border-gray-200 transition-colors"
                >
                  Example: Ambiguous
                </button>
              </div>
            </div>

            {error && (
              <div className="mt-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded text-sm">
                {error}
              </div>
            )}
          </div>
        )}

        {/* Results Column */}
        <div className={`${mode === 'evaluation' ? 'xl:col-span-12' : 'xl:col-span-8'} bg-transparent`}>
          {mode === 'single' ? (
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 h-full flex flex-col">
              <h2 className="text-xl font-semibold mb-4 border-b pb-2 text-gray-800">Result</h2>
              {singleResponse ? (
                renderSingleResult(singleResponse)
              ) : (
                <div className="flex-1 flex items-center justify-center text-gray-400 italic">
                  {loading ? 'Waiting for response...' : 'Run a query to see the result here'}
                </div>
              )}
            </div>
          ) : mode === 'compare' ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 h-full">
              {['rule_v0', 'rule_v1', 'rule_v2'].map((routerId, index) => {
                const comp = compareResponse?.comparisons?.find(c => c.router_id === routerId);
                const title = `Rule V${index}`;
                
                return (
                  <div key={routerId} className="bg-white p-5 rounded-lg shadow-sm border border-gray-200 flex flex-col">
                    <h2 className="text-lg font-semibold mb-3 border-b pb-2 text-gray-800 flex justify-between items-center">
                      {title}
                      {comp?.error && <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">Error</span>}
                    </h2>
                    
                    {!compareResponse ? (
                       <div className="flex-1 flex items-center justify-center text-gray-400 italic text-sm text-center">
                         {loading ? 'Comparing...' : 'No data'}
                       </div>
                    ) : comp?.error ? (
                       <div className="text-red-600 text-sm">{comp.error}</div>
                    ) : comp?.response ? (
                       renderSingleResult(comp.response)
                    ) : null}
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="h-full">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">Evaluation Dashboard</h2>
                <button 
                  onClick={handleRun}
                  disabled={loading}
                  className={`py-2 px-6 rounded font-medium text-white transition-colors ${loading ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}
                >
                  {loading ? 'Running Evaluation...' : 'Run Evaluation on Dataset'}
                </button>
              </div>

              {/* Dataset Selection & Upload */}
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 mb-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Select Dataset */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Select Dataset</h3>
                    <select 
                      value={selectedDatasetId}
                      onChange={e => setSelectedDatasetId(e.target.value)}
                      className="w-full border border-gray-300 rounded p-2 bg-gray-50 focus:ring-2 focus:ring-blue-500 outline-none mb-2"
                    >
                      {datasets.map(d => (
                        <option key={d.dataset_id} value={d.dataset_id}>
                          {d.name} ({d.total_samples} samples) - {d.format}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-gray-500">Choose a dataset to evaluate the routers on.</p>
                  </div>

                  {/* Upload Dataset */}
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 mb-2">Upload Custom Dataset</h3>
                    <div className="flex items-center gap-2 mb-2">
                      <label className={`flex items-center justify-center border border-gray-300 rounded px-4 py-2 cursor-pointer transition-colors text-sm ${uploadingDataset ? 'bg-gray-100 text-gray-400' : 'bg-white hover:bg-gray-50 text-gray-700'}`}>
                        {uploadingDataset ? 'Uploading...' : 'Choose .jsonl or .json File'}
                        <input type="file" accept=".jsonl,.json" className="hidden" onChange={handleUpload} disabled={uploadingDataset} />
                      </label>
                    </div>
                    <p className="text-xs text-gray-500 mb-2">Files must match the required schema. Max 10MB.</p>
                    
                    {uploadResult && (
                      <div className={`mt-2 p-3 rounded text-sm border ${uploadResult.status === 'valid' ? 'bg-green-50 text-green-800 border-green-200' : 'bg-red-50 text-red-800 border-red-200'}`}>
                        <div className="font-semibold mb-1">Upload {uploadResult.status === 'valid' ? 'Successful' : 'Failed'}</div>
                        <div>Valid samples: {uploadResult.valid_samples} | Invalid: {uploadResult.invalid_samples}</div>
                        {uploadResult.errors && uploadResult.errors.length > 0 && (
                          <div className="mt-2 text-xs">
                            <div className="font-semibold text-red-700 mb-1">Top Errors:</div>
                            <ul className="list-disc pl-4 space-y-1">
                              {uploadResult.errors.map((err, i) => (
                                <li key={i}>Line {err.line}: {err.message}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {error && (
                <div className="mb-4 p-3 bg-red-50 text-red-700 border border-red-200 rounded text-sm">
                  {error}
                </div>
              )}
              {renderEvaluationMode()}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
