import { useState, useEffect } from 'react';
import { useNavigate, useParams, Link } from 'react-router-dom';
import eventService from '../services/eventService';
import bookingService from '../services/bookingService';
import { Calendar, MapPin, Tag, Users, ArrowLeft, Loader2, CheckCircle2 } from 'lucide-react';
import authService from '../services/authService';

function EventDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [event, setEvent] = useState(null);
    const [loading, setLoading] = useState(true);
    const [bookingLoading, setBookingLoading] = useState(false);
    const [error, setError] = useState(null);
    const user = authService.getCurrentUser();

    useEffect(() => {
        const fetchEvent = async () => {
            try {
                const data = await eventService.getEventById(id);
                setEvent(data);
            } catch (err) {
                setError('Failed to load event details.');
            } finally {
                setLoading(false);
            }
        };
        fetchEvent();
    }, [id]);

    const handleBooking = async () => {
        if (!user) {
            navigate('/login');
            return;
        }

        setBookingLoading(true);
        try {
            await bookingService.createBooking({ event: id }, user.access || user.token);
            navigate('/my-bookings');
        } catch (err) {
            setError(err.message || 'Failed to book event.');
        } finally {
            setBookingLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
                <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mb-4" />
                <p className="text-gray-500 font-medium">Fetching event details...</p>
            </div>
        );
    }

    if (error || !event) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
                <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 text-center max-w-md">
                    <p className="text-red-500 font-medium mb-4">{error || 'Event not found'}</p>
                    <Link to="/events" className="text-indigo-600 font-semibold hover:underline flex items-center justify-center gap-2">
                        <ArrowLeft className="w-4 h-4" />
                        Back to Events
                    </Link>
                </div>
            </div>
        );
    }

    const formattedDate = new Date(event.date).toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });

    return (
        <div className="min-h-screen bg-gray-50 pb-20">
            {/* Hero Section */}
            <div className="relative h-[400px] w-full overflow-hidden">
                {event.image ? (
                    <img
                        src={event.image}
                        alt={event.title}
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="w-full h-full bg-indigo-600 flex items-center justify-center">
                        <Tag className="w-32 h-32 text-indigo-400 opacity-20" />
                    </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/40 to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-8">
                    <div className="max-w-7xl mx-auto">
                        <Link to="/events" className="inline-flex items-center gap-2 text-white/80 hover:text-white mb-6 transition-colors">
                            <ArrowLeft className="w-4 h-4" />
                            Back to Events
                        </Link>
                        <div className="flex flex-wrap items-center gap-3 mb-4">
                            <span className="bg-indigo-500 text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
                                {event.category_name || 'Event'}
                            </span>
                        </div>
                        <h1 className="text-4xl md:text-5xl font-extrabold text-white mb-4">{event.title}</h1>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-12">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                    {/* Left Column: Details */}
                    <div className="lg:col-span-2">
                        <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
                            <h2 className="text-2xl font-bold text-gray-900 mb-6">About this event</h2>
                            <div className="prose prose-indigo max-w-none text-gray-600 leading-relaxed">
                                {event.description.split('\n').map((para, i) => (
                                    <p key={i} className="mb-4">{para}</p>
                                ))}
                            </div>

                            <div className="mt-10 pt-10 border-t border-gray-100 grid grid-cols-1 sm:grid-cols-2 gap-8">
                                <div className="flex items-start gap-4">
                                    <div className="bg-indigo-50 p-3 rounded-xl text-indigo-600">
                                        <Calendar className="w-6 h-6" />
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-gray-900">Date and Time</h4>
                                        <p className="text-gray-600 text-sm mt-1">{formattedDate}</p>
                                    </div>
                                </div>
                                <div className="flex items-start gap-4">
                                    <div className="bg-indigo-50 p-3 rounded-xl text-indigo-600">
                                        <MapPin className="w-6 h-6" />
                                    </div>
                                    <div>
                                        <h4 className="font-bold text-gray-900">Location</h4>
                                        <p className="text-gray-600 text-sm mt-1">{event.location}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Booking Card (Sticky) */}
                    <div className="lg:col-span-1">
                        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 sticky top-24">
                            <div className="flex items-center justify-between mb-6">
                                <span className="text-gray-500 font-medium">Ticket Price</span>
                                <span className="text-3xl font-bold text-indigo-600">
                                    {event.price > 0 ? `$${event.price}` : 'Free'}
                                </span>
                            </div>

                            <div className="space-y-4 mb-8">
                                <div className="flex items-center text-sm text-gray-600 gap-2">
                                    <Users className="w-4 h-4 text-indigo-500" />
                                    <span>Limited sets available ({event.capacity} total)</span>
                                </div>
                                <div className="flex items-center text-sm text-gray-600 gap-2">
                                    <CheckCircle2 className="w-4 h-4 text-indigo-500" />
                                    <span>Instant confirmation</span>
                                </div>
                            </div>

                            {user ? (
                                <button
                                    onClick={handleBooking}
                                    disabled={bookingLoading}
                                    className="w-full bg-indigo-600 text-white font-bold py-4 rounded-xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {bookingLoading && <Loader2 className="w-5 h-5 animate-spin" />}
                                    {bookingLoading ? 'Processing...' : 'Get Tickets'}
                                </button>
                            ) : (
                                <Link
                                    to="/login"
                                    className="block w-full text-center bg-gray-900 text-white font-bold py-4 rounded-xl hover:bg-gray-800 transition-all shadow-lg active:scale-[0.98]"
                                >
                                    Login to Book
                                </Link>
                            )}


                            <p className="text-center text-xs text-gray-400 mt-6 px-4">
                                By clicking "Get Tickets", you agree to our Terms of Service and Privacy Policy.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default EventDetail;
