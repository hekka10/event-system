import { useState, useEffect } from 'react';
import bookingService from '../services/bookingService';
import eventService from '../services/eventService';
import authService from '../services/authService';
import { UserPlus, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';

function OfflineBookingForm({ onSuccess }) {
    const [events, setEvents] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(false);
    const user = authService.getCurrentUser();

    const [formData, setFormData] = useState({
        user_email: '',
        event: '',
    });

    useEffect(() => {
        fetchEvents();
    }, []);

    const fetchEvents = async () => {
        try {
            const data = await eventService.getAllEvents();
            setEvents(data);
        } catch (err) {
            console.error('Error fetching events:', err);
        }
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(false);

        try {
            await bookingService.createBooking(formData, user.access || user.token);
            setSuccess(true);
            setFormData({ user_email: '', event: '' });
            if (onSuccess) onSuccess();
        } catch (err) {
            setError(err.message || 'Failed to create offline booking.');
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
                        Booking created successfully!
                    </div>
                )}

                {error && (
                    <div className="bg-red-50 border border-red-100 text-red-600 p-3 rounded-xl flex items-center gap-2 text-sm italic">
                        <AlertCircle className="w-4 h-4" />
                        {error}
                    </div>
                )}

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
                        {events.map(ev => (
                            <option key={ev.id} value={ev.id}>{ev.title}</option>
                        ))}
                    </select>
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-gray-900 text-white font-bold py-3 rounded-xl hover:bg-gray-800 transition-all flex items-center justify-center gap-2 text-sm shadow-md"
                >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Register Attendee'}
                </button>
            </form>
        </div>
    );
}

export default OfflineBookingForm;
