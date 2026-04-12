import { useEffect, useState } from 'react';
import { AlertCircle, CheckCircle2, Loader2, UserPlus } from 'lucide-react';

import authService from '../services/authService';
import bookingService from '../services/bookingService';
import eventService from '../services/eventService';
import { formatNpr } from '../utils/currency';


function OfflineBookingForm({ onSuccess }) {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState('');
  const user = authService.getCurrentUser();

  const [formData, setFormData] = useState({
    username: '',
    user_email: '',
    event: '',
  });
  const selectedEvent = events.find((event) => event.id === formData.event);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const data = await eventService.getAllEvents('', user?.access || user?.token || '');
        setEvents(data.filter((event) => event.is_approved));
      } catch (fetchError) {
        setError(fetchError.message || 'Failed to load events.');
      }
    };

    fetchEvents();
  }, [user]);

  const handleChange = (event) => {
    setFormData((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess('');

    try {
      const response = await bookingService.createOfflineBooking(formData, user.access || user.token);
      setSuccess(
        `Walk-in confirmed for ${response.attendee_email}. Ticket code: ${response.ticket_code}`
      );
      setFormData({ username: '', user_email: '', event: '' });
      onSuccess?.();
    } catch (submitError) {
      setError(submitError.message || 'Failed to create offline booking.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
      <h3 className="text-lg font-bold text-gray-900 mb-6 flex items-center gap-2">
        <UserPlus className="w-5 h-5 text-indigo-500" />
        Offline Booking
      </h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        {success && (
          <div className="bg-green-50 border border-green-100 text-green-600 p-3 rounded-xl flex items-center gap-2 text-sm italic">
            <CheckCircle2 className="w-4 h-4" />
            {success}
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-100 text-red-600 p-3 rounded-xl flex items-center gap-2 text-sm italic">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        <div className="space-y-1">
          <label className="text-xs font-bold text-gray-400 uppercase">Attendee Name</label>
          <input
            type="text"
            name="username"
            placeholder="Walk-in attendee"
            value={formData.username}
            onChange={handleChange}
            className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none text-sm transition-all"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs font-bold text-gray-400 uppercase">User Email</label>
          <input
            type="email"
            name="user_email"
            required
            placeholder="attendee@example.com"
            value={formData.user_email}
            onChange={handleChange}
            className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none text-sm transition-all"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs font-bold text-gray-400 uppercase">Select Event</label>
          <select
            name="event"
            required
            value={formData.event}
            onChange={handleChange}
            className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none text-sm transition-all bg-white"
          >
            <option value="">Choose an event</option>
            {events.map((event) => (
              <option key={event.id} value={event.id}>
                {event.title}
              </option>
            ))}
          </select>
        </div>

        {selectedEvent && (
            <div className="rounded-2xl border border-gray-100 bg-gray-50 p-4 text-sm text-gray-600">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-gray-900">{selectedEvent.title}</span>
              <span className="font-bold text-indigo-600">
                {formatNpr(selectedEvent.price, { allowFree: true })}
              </span>
            </div>
            <div className="mt-2 flex items-center justify-between text-xs uppercase tracking-wide text-gray-400">
              <span>Remaining Seats</span>
              <span>{selectedEvent.remaining_capacity}</span>
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-gray-900 text-white font-bold py-3 rounded-xl hover:bg-gray-800 transition-all flex items-center justify-center gap-2 text-sm shadow-md disabled:opacity-50"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Confirm Walk-in Booking'}
        </button>
      </form>
    </div>
  );
}


export default OfflineBookingForm;
