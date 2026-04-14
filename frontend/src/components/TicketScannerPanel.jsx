import { useState } from 'react';
import { CheckCircle2, Loader2, QrCode, ScanLine, XCircle } from 'lucide-react';

import bookingService from '../services/bookingService';
import useAuth from '../hooks/useAuth';


function TicketScannerPanel({ onSuccess }) {
  const [ticketCode, setTicketCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const { token } = useAuth();

  const runScan = async (markCheckedIn) => {
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const data = await bookingService.scanTicket(
        {
          ticket_code: ticketCode,
          mark_checked_in: markCheckedIn,
        },
        token
      );
      setResult(data);
      onSuccess?.();
      if (markCheckedIn) {
        setTicketCode('');
      }
    } catch (scanError) {
      setError(scanError.message || 'Failed to scan ticket.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
        <ScanLine className="w-5 h-5 text-indigo-500" />
        Ticket Scan & Check-in
      </h3>

      <div className="space-y-4">
        <div className="space-y-1">
          <label className="text-xs font-bold text-gray-400 uppercase">Ticket Code</label>
          <input
            type="text"
            value={ticketCode}
            onChange={(event) => setTicketCode(event.target.value.toUpperCase())}
            placeholder="TICKET-XXXXXXXXXXXX"
            className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none text-sm transition-all"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <button
            type="button"
            disabled={loading || !ticketCode.trim()}
            onClick={() => runScan(false)}
            className="w-full bg-gray-100 text-gray-800 font-semibold py-3 rounded-xl hover:bg-gray-200 transition-all disabled:opacity-50"
          >
            Validate
          </button>
          <button
            type="button"
            disabled={loading || !ticketCode.trim()}
            onClick={() => runScan(true)}
            className="w-full bg-indigo-600 text-white font-semibold py-3 rounded-xl hover:bg-indigo-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <QrCode className="w-4 h-4" />}
            Check In
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-100 text-red-600 p-3 rounded-xl text-sm flex items-start gap-2">
            <XCircle className="w-4 h-4 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        {result && (
          <div className="bg-emerald-50 border border-emerald-100 text-emerald-700 p-4 rounded-xl text-sm">
            <div className="flex items-center gap-2 font-semibold mb-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>{result.message}</span>
            </div>
            <p>Attendee: {result.booking.user_email}</p>
            <p>Event: {result.booking.event_details.title}</p>
            <p>Ticket: {result.ticket.ticket_code}</p>
          </div>
        )}
      </div>
    </div>
  );
}


export default TicketScannerPanel;
