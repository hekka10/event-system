import { Calendar, CheckCircle2, Download, MapPin, QrCode, ScanLine, Ticket } from 'lucide-react';
import { formatDateTime } from '../utils/date';


function TicketPreviewCard({ booking }) {
  const ticket = booking.ticket;
  const qrCodeUrl = ticket?.qr_code_url || ticket?.qr_code;

  if (!ticket) {
    return null;
  }

  return (
    <div className="mt-5 rounded-3xl border border-indigo-100 bg-gradient-to-br from-white via-indigo-50/40 to-slate-50 p-5">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-start gap-4">
          <div className="hidden rounded-2xl bg-indigo-100 p-3 text-indigo-600 sm:flex">
            <Ticket className="h-6 w-6" />
          </div>
          <div>
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="rounded-full bg-indigo-600 px-3 py-1 text-xs font-bold uppercase tracking-[0.2em] text-white">
                QR Ticket
              </span>
              {ticket.is_scanned ? (
                <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold uppercase tracking-wide text-emerald-700">
                  Checked In
                </span>
              ) : (
                <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold uppercase tracking-wide text-amber-700">
                  Ready To Scan
                </span>
              )}
            </div>

            <h3 className="text-xl font-bold text-gray-900">{booking.event_details.title}</h3>
            <p className="mt-1 text-sm text-gray-500">
              Present this QR ticket at the entrance for validation.
            </p>

            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="rounded-2xl bg-white/80 px-4 py-3 shadow-sm">
                <p className="text-xs font-bold uppercase tracking-wide text-gray-400">Ticket Code</p>
                <p className="mt-1 font-mono text-sm font-semibold text-gray-900">{ticket.ticket_code}</p>
              </div>
              <div className="rounded-2xl bg-white/80 px-4 py-3 shadow-sm">
                <p className="text-xs font-bold uppercase tracking-wide text-gray-400">Status</p>
                <p className="mt-1 text-sm font-semibold text-gray-900">
                  {ticket.is_scanned ? 'Already scanned at venue' : 'Valid and ready for entry'}
                </p>
              </div>
              <div className="rounded-2xl bg-white/80 px-4 py-3 shadow-sm">
                <p className="text-xs font-bold uppercase tracking-wide text-gray-400">Event Date</p>
                <p className="mt-1 flex items-center gap-2 text-sm text-gray-700">
                  <Calendar className="h-4 w-4 text-indigo-500" />
                  {formatDateTime(booking.event_details.date)}
                </p>
              </div>
              <div className="rounded-2xl bg-white/80 px-4 py-3 shadow-sm">
                <p className="text-xs font-bold uppercase tracking-wide text-gray-400">Venue</p>
                <p className="mt-1 flex items-center gap-2 text-sm text-gray-700">
                  <MapPin className="h-4 w-4 text-indigo-500" />
                  {booking.event_details.location}
                </p>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-3">
              {qrCodeUrl && (
                <a
                  href={qrCodeUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 rounded-xl bg-gray-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-gray-800"
                >
                  <Download className="h-4 w-4" />
                  Open QR Image
                </a>
              )}
              <span className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-sm font-semibold text-gray-700 shadow-sm">
                {ticket.is_scanned ? <CheckCircle2 className="h-4 w-4 text-emerald-500" /> : <ScanLine className="h-4 w-4 text-indigo-500" />}
                {ticket.is_scanned ? 'Entry recorded' : 'Scan at gate'}
              </span>
            </div>
          </div>
        </div>

        <div className="flex justify-center lg:justify-end">
          <div className="rounded-[2rem] border border-indigo-100 bg-white p-4 shadow-sm">
            {qrCodeUrl ? (
              <img
                src={qrCodeUrl}
                alt={`QR ticket for ${booking.event_details.title}`}
                className="h-52 w-52 rounded-2xl object-contain"
              />
            ) : (
              <div className="flex h-52 w-52 flex-col items-center justify-center rounded-2xl bg-gray-50 text-gray-400">
                <QrCode className="mb-3 h-10 w-10" />
                <p className="text-sm font-medium">QR code unavailable</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


export default TicketPreviewCard;
