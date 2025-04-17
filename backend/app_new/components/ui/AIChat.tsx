'use client';
import { useState, useEffect } from 'react';
import { useMapContext } from '@/context/MapContext';
import ReactMarkdown from 'react-markdown';

export default function AIChat() {
  const { bounds } = useMapContext();
  const [input, setInput] = useState('');
  const [response, setResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [tokenBalance, setTokenBalance] = useState<number | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState<boolean>(false);

  // Fetch the balance from the balance endpoint if token exists.
  const fetchBalance = async () => {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const res = await fetch('http://localhost:8004/balance', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      if (!res.ok) {
        throw new Error('Error fetching balance');
      }
      const data = await res.json();
      setTokenBalance(data.credits);
    } catch (err) {
      console.error('Balance fetch error:', err);
      setTokenBalance(null);
    }
  };

  // On mount, check if user is logged in (i.e., token exists) and fetch balance.
  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (token) { // TODO: Check if token is valid, not just assume
      setIsLoggedIn(true);
      fetchBalance();
    } else {
      setIsLoggedIn(false);
      setTokenBalance(null);
    }
  }, []);

  const handleSubmit = async () => {
    if (!bounds || !input.trim()) return;
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token) {
      setResponse("You must be logged in to use this feature.");
      return;
    }

    setLoading(true);
    setResponse(null);

    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();

    try {
      const res = await fetch('http://127.0.0.1:8002/summary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          question: input,
          sw_lat: sw.lat,
          sw_lon: sw.lng,
          ne_lat: ne.lat,
          ne_lon: ne.lng,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        console.log('Error response:', errorData);
        throw new Error(errorData.detail || 'Something went wrong');
      }

      const { job_id, remaining_credits } = await res.json();
      setTokenBalance(remaining_credits);

      const result_event = new EventSource(`http://${window.location.hostname}/ai/stream/${job_id}`);
      result_event.onmessage = (event) => {
        console.log('EventSource message:', event.data);
        const { message } = JSON.parse(event.data);
        setResponse(message);
        setLoading(false);
        fetchBalance(); // In case of refund
        result_event.close();
      }

      result_event.onerror = (error) => {
        console.error('EventSource error:', error);
        setResponse('Error receiving AI response.');
        setLoading(false);
        fetchBalance();
        result_event.close();
      }

    } catch (err) {
      console.error('Fetch error:', err);
      setResponse(`Error fetching AI response: ${err}`);
      setLoading(false);
      await fetchBalance();
    } finally {
      setInput('');
    }
  };

  return (
      <div className="flex flex-col h-full w-full bg-white shadow-md border-r border-gray-200">
        <div className="p-2 bg-gray-200 text-sm text-center">
          {isLoggedIn ? (
              tokenBalance !== null ? (
                  <>
                    You have {tokenBalance} credits.<br/>
                    Each request takes 25 credits.
                  </>
              ) : (
                  'Loading token balance...'
              )
          ) : (
              'You are not logged in. Please log in to use this feature.'
          )}
        </div>
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
            disabled={!isLoggedIn}
        />
          <button
              className="mt-2 w-full bg-blue-600 hover:bg-blue-700 text-white text-sm py-2 rounded disabled:opacity-50"
              onClick={handleSubmit}
              disabled={loading || !input.trim() || !isLoggedIn}
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
  );
}