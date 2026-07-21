"use client";

import { useEffect, useState } from 'react';
import {
  deleteOpenRouterRuntimeKey,
  getOpenRouterStatus,
  setOpenRouterKey,
  verifyOpenRouterKey,
  OpenRouterStatus,
} from '@/lib/api';

interface Props {
  onRoutersRefresh?: () => Promise<void> | void;
}

export default function OpenRouterConfigCard({ onRoutersRefresh }: Props) {
  const [apiKey, setApiKey] = useState('');
  const [status, setStatus] = useState<OpenRouterStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = async () => {
    try {
      setStatus(await getOpenRouterStatus());
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Không thể đọc trạng thái OpenRouter');
    }
  };

  useEffect(() => {
    // The status is external backend state and must be loaded once on mount.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void refresh();
  }, []);

  const handleVerify = async () => {
    if (!apiKey.trim()) return;
    setBusy(true);
    setMessage(null);
    try {
      await verifyOpenRouterKey(apiKey);
      setMessage('API key hợp lệ. Key chưa được lưu.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Verify thất bại');
    } finally {
      await refresh();
      await onRoutersRefresh?.();
      setApiKey('');
      setBusy(false);
    }
  };

  const handleSave = async () => {
    if (!apiKey.trim()) return;
    setBusy(true);
    setMessage(null);
    try {
      setStatus(await setOpenRouterKey(apiKey));
      setMessage('Đã cấu hình runtime key trong memory backend.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Không thể lưu runtime key');
    } finally {
      await refresh();
      await onRoutersRefresh?.();
      setApiKey('');
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    setBusy(true);
    setMessage(null);
    try {
      setStatus(await deleteOpenRouterRuntimeKey());
      setMessage('Đã xóa runtime key.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Không thể xóa runtime key');
    } finally {
      await refresh();
      await onRoutersRefresh?.();
      setBusy(false);
    }
  };

  return (
    <section className="bg-white p-6 rounded-lg shadow-sm border border-gray-200 space-y-4">
      <div>
        <h2 className="text-xl font-bold text-gray-800">OpenRouter Configuration</h2>
        <p className="text-sm text-gray-500 mt-1">Key chỉ được giữ trong memory backend và không lưu vào trình duyệt.</p>
      </div>

      <div className="text-sm rounded border bg-gray-50 p-3">
        <div><span className="font-semibold">Trạng thái:</span> {status?.connection_status || 'Đang kiểm tra...'}</div>
        <div><span className="font-semibold">Nguồn:</span> {status?.source || 'Chưa cấu hình'}</div>
      </div>

      {status?.last_checked_at && (
        <div className="text-xs text-gray-500">
          Last checked: {new Date(status.last_checked_at).toLocaleString('vi-VN')}
        </div>
      )}

      {status?.error_code && (
        <div className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">
          <div className="font-semibold">Connection error</div>
          <div>Code: {status.error_code}</div>
          {status.error_message && <div>{status.error_message}</div>}
        </div>
      )}

      <label className="block text-sm font-semibold text-gray-700">
        OpenRouter API key
        <input
          type="password"
          autoComplete="off"
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          className="mt-2 w-full border border-gray-300 rounded-md p-2.5 font-normal"
          placeholder="sk-or-..."
        />
      </label>

      <div className="flex flex-wrap gap-3">
        <button onClick={handleVerify} disabled={busy || !apiKey.trim()} className="px-4 py-2 rounded bg-gray-700 text-white disabled:opacity-50">Verify, không lưu</button>
        <button onClick={handleSave} disabled={busy || !apiKey.trim()} className="px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50">Lưu runtime key</button>
        <button onClick={handleDelete} disabled={busy} className="px-4 py-2 rounded border border-red-300 text-red-700 disabled:opacity-50">Xóa runtime key</button>
      </div>
      {message && <p className="text-sm text-gray-700" role="status">{message}</p>}
    </section>
  );
}
