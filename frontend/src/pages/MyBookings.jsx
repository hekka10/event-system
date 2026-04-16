import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import AlertMessage from '../components/AlertMessage';
import bookingService from '../services/bookingService';
import useAuth from '../hooks/useAuth';
import TicketPreviewCard from '../components/TicketPreviewCard';
import { formatNpr } from '../utils/currency';
import { formatDateTime } from '../utils/date';
import {
    ArrowRight,
    Calendar,
    CheckCircle2,
    Clock3,
    ExternalLink,
    Loader2,
    Mail,
    MapPin,
    QrCode,
    Receipt,
    ScanLine,
    Ticket,
    XCircle,
} from 'lucide-react';

const STATUS_FILTERS = ['ALL', 'CONFIRMED', 'PENDING', 'CANCELLED', 'FAILED'];

const formatPrice = (value) => formatNpr(value);

const getStatusMeta = (booking) => {
    if (booking.status === 'CONFIRMED') {
        return {
            label: 'Confirmed',
            className: 'bg-emerald-500 text-white',
            description: booking.ticket?.is_scanned
                ? 'Checked in at the venue.'
                : 'Your seat is reserved and ticket is ready.',
        };
    }

    if (booking.status === 'FAILED') {
        return {
            label: 'Failed',
            className: 'bg-rose-500 text-white',
            description: 'This booking did not complete successfully.',
        };
    }

    if (booking.status === 'CANCELLED') {
        return {
            label: 'Cancelled',
            className: 'bg-slate-500 text-white',
            description: 'This booking was cancelled. You can book the event again if seats are available.',
        };
    }

    return {
        label: 'Pending',
        className: 'bg-amber-500 text-white',
        description: booking.latest_payment?.status === 'FAILED'
            ? 'Payment failed. Start a new booking from the event page.'
            : 'Waiting for payment confirmation.',
    };
};

const getCancellationNotice = (booking) => {
    if (
        booking.can_cancel
        || !booking.cancellation_error
        || booking.status === 'CANCELLED'
        || booking.status === 'FAILED'
    ) {
        return null;
    }

    return booking.cancellation_error;
};

function MyBookings() {
    const [bookings, setBookings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [notice, setNotice] = useState('');
    const [statusFilter, setStatusFilter] = useState('ALL');
    const [expandedTicketBookingId, setExpandedTicketBookingId] = useState(null);
    const [emailingBookingId, setEmailingBookingId] = useState(null);
    const [cancelingBookingId, setCancelingBookingId] = useState(null);
    const { token } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        setNotice(location.state?.message || '');
    }, [location.state]);

    useEffect(() => {
        if (!token) {
            navigate('/login');
            return;
        }
        const loadBookings = async () => {
            try {
                const data = await bookingService.getMyBookings(token);
                setBookings(data);
                setError(null);
            } catch {
                setError('Failed to load your bookings.');
            } finally {
                setLoading(false);
            }
        };

        loadBookings();
    }, [navigate, token]);

    const fetchBookings = async () => {
        try {
            setError(null);
            const data = await bookingService.getMyBookings(token);
            setBookings(data);
        } catch {
            setError('Failed to load your bookings.');
        } finally {
            setLoading(false);
        }
    };

    const filteredBookings = bookings.filter((booking) => {
        if (statusFilter === 'ALL') {
            return true;
        }

        return booking.status === statusFilter;
    });

    const handleSendTicketEmail = async (bookingId) => {
        setEmailingBookingId(bookingId);
        setError(null);
        setNotice('');

        try {
            const response = await bookingService.sendTicketEmail(bookingId, token);
            setNotice(response.message || 'Ticket email sent successfully.');
        } catch (sendError) {
            setError(sendError.message || 'Failed to send ticket email.');
        } finally {
            setEmailingBookingId(null);
        }
    };

    const handleCancelBooking = async (booking) => {
        const confirmationMessage = booking.status === 'CONFIRMED'
            ? 'Cancel this confirmed booking? Your ticket will no longer be valid for entry.'
            : 'Cancel this booking?';

        if (!window.confirm(confirmationMessage)) {
            return;
        }

        setCancelingBookingId(booking.id);
        setError(null);
        setNotice('');

        try {
            const response = await bookingService.cancelBooking(booking.id, token);
            setBookings((currentBookings) => currentBookings.map((currentBooking) => (
                currentBooking.id === booking.id ? response.booking : currentBooking
            )));
            setExpandedTicketBookingId((currentId) => (
                currentId === booking.id ? null : currentId
            ));
            setNotice(response.message || 'Booking cancelled successfully.');
        } catch (cancelError) {
            setError(cancelError.message || 'Failed to cancel booking.');
        } finally {
            setCancelingBookingId(null);
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
                    <AlertMessage
                        variant="error"
                        centered
                        className="mb-8 p-6"
                        actions={(
                            <button onClick={fetchBookings} className="font-bold underline">
                                Try again
                            </button>
                        )}
                    >
                        {error}
                    </AlertMessage>
                )}

                {notice && (
                    <AlertMessage variant="success" centered className="mb-8 p-6">
                        {notice}
                    </AlertMessage>
                )}

                {bookings.length > 0 && (
                    <>
                        <div className="mb-8 flex flex-wrap gap-3">
                            {STATUS_FILTERS.map((filterValue) => (
                                <button
                                    key={filterValue}
                                    type="button"
                                    onClick={() => setStatusFilter(filterValue)}
                                    className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
                                        statusFilter === filterValue
                                            ? 'bg-indigo-600 text-white'
                                            : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                                    }`}
                                >
                                    {filterValue === 'ALL' ? 'All Bookings' : filterValue.charAt(0) + filterValue.slice(1).toLowerCase()}
                                </button>
                            ))}
                        </div>
                    </>
                )}

                {filteredBookings.length > 0 ? (
                    <div className="space-y-6">
                        {filteredBookings.map((booking) => {
                            const statusMeta = getStatusMeta(booking);
                            const cancellationNotice = getCancellationNotice(booking);

                            return (
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
                                            <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider shadow-sm ${statusMeta.className}`}>
                                            {statusMeta.label}
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
                                            <span className="text-lg font-bold text-indigo-600">{formatPrice(booking.total_price)}</span>
                                        </div>

                                        <p className="text-sm text-gray-500 mb-4">{statusMeta.description}</p>

                                        {cancellationNotice && (
                                            <div className="mb-4 inline-flex items-start gap-2 rounded-xl bg-amber-50 px-3 py-2 text-sm font-medium text-amber-800">
                                                <Clock3 className="mt-0.5 h-4 w-4 shrink-0" />
                                                <span>{cancellationNotice}</span>
                                            </div>
                                        )}

                                        <div className="flex flex-wrap gap-4 text-sm text-gray-500 mb-4">
                                            <div className="flex items-center gap-1.5">
                                                <Calendar className="w-4 h-4 text-indigo-400" />
                                                {formatDateTime(booking.event_details.date)}
                                            </div>
                                            <div className="flex items-center gap-1.5">
                                                <MapPin className="w-4 h-4 text-indigo-400" />
                                                {booking.event_details.location}
                                            </div>
                                        </div>

                                        <div className="flex flex-wrap gap-3 text-xs font-semibold uppercase tracking-wide text-gray-500 mb-4">
                                            <span className="bg-gray-100 px-3 py-1 rounded-full">
                                                {booking.booking_source}
                                            </span>
                                            {booking.is_student && (
                                                <span className="bg-emerald-50 text-emerald-700 px-3 py-1 rounded-full">
                                                    Student Discount
                                                </span>
                                            )}
                                            {booking.ticket?.is_scanned && (
                                                <span className="bg-indigo-50 text-indigo-700 px-3 py-1 rounded-full">
                                                    Checked In
                                                </span>
                                            )}
                                            {booking.latest_payment && (
                                                <span className="bg-slate-100 text-slate-700 px-3 py-1 rounded-full">
                                                    Payment {booking.latest_payment.status}
                                                </span>
                                            )}
                                        </div>

                                        {booking.discount_amount > 0 && (
                                            <p className="text-sm text-emerald-600 font-medium mb-4">
                                                Saved {formatPrice(booking.discount_amount)} with verified student pricing.
                                            </p>
                                        )}

                                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm text-gray-600">
                                            <div className="rounded-xl bg-gray-50 px-4 py-3">
                                                <p className="text-xs uppercase tracking-wide text-gray-400 font-bold mb-1">Booked On</p>
                                                <p>{formatDateTime(booking.created_at)}</p>
                                            </div>
                                            <div className="rounded-xl bg-gray-50 px-4 py-3">
                                                <p className="text-xs uppercase tracking-wide text-gray-400 font-bold mb-1">Confirmed On</p>
                                                <p>{booking.confirmed_at ? formatDateTime(booking.confirmed_at) : 'Awaiting confirmation'}</p>
                                            </div>
                                            <div className="rounded-xl bg-gray-50 px-4 py-3">
                                                <p className="text-xs uppercase tracking-wide text-gray-400 font-bold mb-1">Payment Status</p>
                                                <p>{booking.latest_payment?.status || 'Not started'}</p>
                                            </div>
                                            <div className="rounded-xl bg-gray-50 px-4 py-3">
                                                <p className="text-xs uppercase tracking-wide text-gray-400 font-bold mb-1">Ticket Code</p>
                                                <p>{booking.ticket?.ticket_code || 'Generated after confirmation'}</p>
                                            </div>
                                            <div className="rounded-xl bg-gray-50 px-4 py-3">
                                                <p className="text-xs uppercase tracking-wide text-gray-400 font-bold mb-1">Base Price</p>
                                                <p>{formatPrice(booking.base_price)}</p>
                                            </div>
                                            <div className="rounded-xl bg-gray-50 px-4 py-3">
                                                <p className="text-xs uppercase tracking-wide text-gray-400 font-bold mb-1">Discount</p>
                                                <p className={booking.discount_amount > 0 ? 'text-emerald-600 font-semibold' : ''}>
                                                    -{formatPrice(booking.discount_amount)}
                                                </p>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="pt-6 border-t border-gray-50 flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                                        <div className="flex flex-wrap items-center gap-3">
                                            {booking.ticket && booking.status === 'CONFIRMED' && (
                                                <button
                                                    type="button"
                                                    onClick={() => setExpandedTicketBookingId((currentId) => (
                                                        currentId === booking.id ? null : booking.id
                                                    ))}
                                                    className="flex items-center gap-2 text-sm font-semibold text-gray-700 bg-gray-50 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
                                                >
                                                    {expandedTicketBookingId === booking.id ? <ScanLine className="w-4 h-4" /> : <QrCode className="w-4 h-4" />}
                                                    {expandedTicketBookingId === booking.id ? 'Hide Ticket' : 'Show Ticket'}
                                                </button>
                                            )}
                                            {booking.ticket && booking.status === 'CONFIRMED' && (
                                                <button
                                                    type="button"
                                                    disabled={emailingBookingId === booking.id}
                                                    onClick={() => handleSendTicketEmail(booking.id)}
                                                    className="flex items-center gap-2 text-sm font-semibold text-emerald-700 bg-emerald-50 px-4 py-2 rounded-lg hover:bg-emerald-100 transition-colors disabled:opacity-60"
                                                >
                                                    {emailingBookingId === booking.id ? (
                                                        <Loader2 className="w-4 h-4 animate-spin" />
                                                    ) : (
                                                        <Mail className="w-4 h-4" />
                                                    )}
                                                    {emailingBookingId === booking.id ? 'Sending Email...' : 'Send Ticket Email'}
                                                </button>
                                            )}
                                            {booking.can_cancel && (
                                                <button
                                                    type="button"
                                                    disabled={cancelingBookingId === booking.id}
                                                    onClick={() => handleCancelBooking(booking)}
                                                    className="flex items-center gap-2 text-sm font-semibold text-rose-700 bg-rose-50 px-4 py-2 rounded-lg hover:bg-rose-100 transition-colors disabled:opacity-60"
                                                >
                                                    {cancelingBookingId === booking.id ? (
                                                        <Loader2 className="w-4 h-4 animate-spin" />
                                                    ) : (
                                                        <XCircle className="w-4 h-4" />
                                                    )}
                                                    {cancelingBookingId === booking.id ? 'Cancelling...' : 'Cancel Booking'}
                                                </button>
                                            )}
                                            {booking.ticket?.is_scanned && (
                                                <span className="flex items-center gap-2 text-sm font-semibold text-indigo-700 bg-indigo-50 px-4 py-2 rounded-lg">
                                                    <CheckCircle2 className="w-4 h-4" />
                                                    Checked In
                                                </span>
                                            )}
                                            {booking.latest_payment && booking.status === 'PENDING' && booking.latest_payment.status !== 'FAILED' && (
                                                <Link
                                                    to={`/checkout/${booking.latest_payment.id}`}
                                                    className="flex items-center gap-2 text-sm font-semibold text-indigo-600 bg-indigo-50 px-4 py-2 rounded-lg hover:bg-indigo-100 transition-colors"
                                                >
                                                    <Clock3 className="w-4 h-4" />
                                                    Pay Now
                                                </Link>
                                            )}
                                            {(booking.status === 'FAILED' || booking.status === 'CANCELLED') && (
                                                <Link
                                                    to={`/events/${booking.event}`}
                                                    className="flex items-center gap-2 text-sm font-semibold text-rose-600 bg-rose-50 px-4 py-2 rounded-lg hover:bg-rose-100 transition-colors"
                                                >
                                                    <XCircle className="w-4 h-4" />
                                                    Book Again
                                                </Link>
                                            )}
                                            {booking.latest_payment && (
                                                <span className="flex items-center gap-2 text-sm font-semibold text-gray-700 bg-gray-50 px-4 py-2 rounded-lg">
                                                    <Receipt className="w-4 h-4" />
                                                    {booking.latest_payment.provider}
                                                </span>
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

                                    {expandedTicketBookingId === booking.id && booking.ticket && (
                                        <TicketPreviewCard booking={booking} />
                                    )}
                                </div>
                            </div>
                        )})}
                    </div>
                ) : bookings.length > 0 ? (
                    <div className="bg-white rounded-3xl border border-dashed border-gray-300 p-16 text-center">
                        <div className="bg-indigo-50 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6">
                            <Ticket className="w-10 h-10 text-indigo-400" />
                        </div>
                        <h3 className="text-xl font-bold text-gray-900 mb-2">No bookings in this filter</h3>
                        <p className="text-gray-500 mb-8 max-w-sm mx-auto">
                            Switch filters to view your other bookings and ticket statuses.
                        </p>
                        <button
                            type="button"
                            onClick={() => setStatusFilter('ALL')}
                            className="inline-flex bg-indigo-600 text-white font-bold px-8 py-3 rounded-xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100"
                        >
                            Show All Bookings
                        </button>
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
