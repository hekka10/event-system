import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import bookingService from '../services/bookingService';
import authService from '../services/authService';
import { Calendar, MapPin, Ticket, Loader2, ExternalLink, QrCode, ArrowRight } from 'lucide-react';

function MyBookings() {
    const [bookings, setBookings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const user = authService.getCurrentUser();
    const navigate = useNavigate();

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }
        fetchBookings();
    }, []);

    const fetchBookings = async () => {
        try {
            const data = await bookingService.getMyBookings(user.access || user.token);
            setBookings(data);
        } catch (err) {
            setError('Failed to load your bookings.');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
                <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mb-4" />
                <p className="text-gray-500 font-medium">Loading your bookings...</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-5xl mx-auto">
                <div className="flex items-center justify-between mb-10">
                    <div>
                        <h1 className="text-3xl font-extrabold text-gray-900">My Bookings</h1>
                        <p className="mt-2 text-gray-500 font-medium">Manage your event registrations and tickets</p>
                    </div>
                    <Link
                        to="/events"
                        className="flex items-center gap-2 text-indigo-600 font-semibold hover:text-indigo-700 underline underline-offset-4"
                    >
                        Find more events
                        <ArrowRight className="w-4 h-4" />
                    </Link>
                </div>

                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-600 p-6 rounded-2xl text-center mb-8">
                        <p>{error}</p>
                        <button onClick={fetchBookings} className="mt-2 font-bold underline">Try again</button>
                    </div>
                )}

                {bookings.length > 0 ? (
                    <div className="space-y-6">
                        {bookings.map((booking) => (
                            <div key={booking.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden flex flex-col md:flex-row">
                                {/* Event Image / Placeholder */}
                                <div className="w-full md:w-56 h-48 md:h-auto bg-gray-100 relative shrink-0">
                                    {booking.event_details.image ? (
                                        <img src={booking.event_details.image} alt={booking.event_details.title} className="w-full h-full object-cover" />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center text-gray-300">
                                            <Ticket className="w-12 h-12" />
                                        </div>
                                    )}
                                    <div className="absolute top-4 left-4">
                                        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider shadow-sm
                      ${booking.status === 'CONFIRMED' ? 'bg-green-500 text-white' : 'bg-yellow-500 text-white'}`}>
                                            {booking.status}
                                        </span>
                                    </div>
                                </div>

                                {/* Content */}
                                <div className="p-6 grow flex flex-col justify-between">
                                    <div>
                                        <div className="flex justify-between items-start mb-2">
                                            <Link to={`/events/${booking.event}`} className="text-xl font-bold text-gray-900 hover:text-indigo-600 transition-colors">
                                                {booking.event_details.title}
                                            </Link>
                                            <span className="text-lg font-bold text-indigo-600">${booking.total_price}</span>
                                        </div>

                                        <div className="flex flex-wrap gap-4 text-sm text-gray-500 mb-4">
                                            <div className="flex items-center gap-1.5">
                                                <Calendar className="w-4 h-4 text-indigo-400" />
                                                {new Date(booking.event_details.date).toLocaleDateString()}
                                            </div>
                                            <div className="flex items-center gap-1.5">
                                                <MapPin className="w-4 h-4 text-indigo-400" />
                                                {booking.event_details.location}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="pt-6 border-t border-gray-50 flex items-center justify-between">
                                        <div className="flex items-center gap-4">
                                            {booking.ticket && (
                                                <a
                                                    href={booking.ticket.qr_code}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="flex items-center gap-2 text-sm font-semibold text-gray-700 bg-gray-50 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                                                >
                                                    <QrCode className="w-4 h-4" />
                                                    View Ticket
                                                </a>
                                            )}
                                        </div>
                                        <Link
                                            to={`/events/${booking.event}`}
                                            className="text-sm font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                                        >
                                            Event Page
                                            <ExternalLink className="w-4 h-4" />
                                        </Link>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="bg-white rounded-3xl border border-dashed border-gray-300 p-16 text-center">
                        <div className="bg-indigo-50 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
                            <Ticket className="w-10 h-10 text-indigo-400" />
                        </div>
                        <h3 className="text-xl font-bold text-gray-900 mb-2">No bookings yet</h3>
                        <p className="text-gray-500 mb-8 max-w-sm mx-auto">Explore upcoming events and reserve your spot today!</p>
                        <Link
                            to="/events"
                            className="inline-flex bg-indigo-600 text-white font-bold px-8 py-3 rounded-xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100"
                        >
                            Browse Events
                        </Link>
                    </div>
                )}
            </div>
        </div>
    );
}

export default MyBookings;
