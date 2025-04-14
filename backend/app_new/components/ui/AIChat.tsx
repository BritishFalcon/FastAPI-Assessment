'use client';
import { useState } from 'react';
import { useMapContext } from '@/context/MapContext';
import ReactMarkdown from 'react-markdown';

export default function AIChat() {
  const { bounds } = useMapContext();
  const [input, setInput] = useState('');
  const [response, setResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!bounds || !input.trim()) return;

    setLoading(true);
    setResponse(null);

    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();

    try {
      const res = await fetch('http://127.0.0.1:8002/summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: input,
          sw_lat: sw.lat,
          sw_lon: sw.lng,
          ne_lat: ne.lat,
          ne_lon: ne.lng,
        }),
      });

      const data = await res.text();
      setResponse(data);
    } catch (err) {
      console.error('Fetch error:', err);
      setResponse(`Error fetching AI response: ${err}`);
    } finally {
      setLoading(false);
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-white shadow-md border-r border-gray-200">
      <div className="flex-1 overflow-auto p-4 space-y-4">
        {loading && <p className="text-sm text-gray-500">Thinking...</p>}
        {response && (
          <div className="text-sm bg-gray-100 p-3 rounded">
            <ReactMarkdown>{response}</ReactMarkdown>
          </div>
        )}
      </div>
      <div className="border-t p-4">
        <textarea
          className="w-full border border-gray-300 p-2 rounded resize-none text-sm"
          rows={3}
          placeholder="Ask something about the map..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
        />
        <button
          className="mt-2 w-full bg-blue-600 hover:bg-blue-700 text-white text-sm py-2 rounded disabled:opacity-50"
          onClick={handleSubmit}
          disabled={loading || !input.trim()}
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
}