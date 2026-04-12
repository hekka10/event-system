import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  CarFront,
  CheckCircle2,
  Edit3,
  Loader2,
  MapPin,
  Navigation,
  Tag,
  Trash2,
  Users,
} from 'lucide-react';

import EventLocationMap from '../components/EventLocationMap';
import authService from '../services/authService';
import bookingService from '../services/bookingService';
import eventService from '../services/eventService';
import { formatNpr } from '../utils/currency';


function EventDetail() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [bookingLoading, setBookingLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);
  const [actionError, setActionError] = useState(null);
  const [notice, setNotice] = useState(location.state?.message || '');
  const user = authService.getCurrentUser();
  const token = user?.access || user?.token || '';
  const isAdmin = authService.isAdmin(user);

  useEffect(() => {
    setNotice(location.state?.message || '');
  }, [location.state]);

  useEffect(() => {
    const fetchEvent = async () => {
      try {
        const data = await eventService.getEventById(id, token);
        setEvent(data);
        setLoadError(null);
      } catch (fetchError) {
        setLoadError(fetchError.message || 'Failed to load event details.');
      } finally {
        setLoading(false);
      }
    };

    fetchEvent();
  }, [id, token]);

  const handleBooking = async () => {
    if (!user) {
      navigate('/login', { state: { from: { pathname: `/events/${id}` } } });
      return;
    }

    setBookingLoading(true);
    setActionError(null);
    setNotice('');

    try {
      const response = await bookingService.initiatePayment(
        { event: id },
        token
      );

      if (response.next_action === 'CONFIRMED') {
        navigate('/my-bookings', {
          state: { message: 'Booking confirmed successfully.' },
        });
        return;
      }

      navigate(`/checkout/${response.payment.id}`, {
        state: { message: 'Booking created. Complete payment to confirm your ticket.' },
      });
    } catch (bookingError) {
      setActionError(bookingError.message || 'Failed to start checkout.');
    } finally {
      setBookingLoading(false);
    }
  };

  const handleApprove = async () => {
    setActionLoading(true);
    setActionError(null);
    setNotice('');

    try {
      const updatedEvent = await eventService.approveEvent(id, token);
      setEvent(updatedEvent);
      setNotice('Event approved successfully.');
    } catch (approveError) {
      setActionError(approveError.message || 'Failed to approve event.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    const confirmed = window.confirm('Delete this event? This action cannot be undone.');
    if (!confirmed) {
      return;
    }

    setActionLoading(true);
    setActionError(null);
    setNotice('');

    try {
      await eventService.deleteEvent(id, token);
      navigate('/events', {
        replace: true,
        state: { message: 'Event deleted successfully.' },
      });
    } catch (deleteError) {
      setActionError(deleteError.message || 'Failed to delete event.');
      setActionLoading(false);
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

  if (loadError || !event) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 px-4">
        <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 text-center max-w-md">
          <p className="text-red-500 font-medium mb-4">{loadError || 'Event not found'}</p>
          <Link to="/events" className="text-indigo-600 font-semibold hover:underline inline-flex items-center justify-center gap-2">
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
    minute: '2-digit',
  });
  const googleMapsLink = event.google_maps_link || event.parking_map_url;
  const canManageEvent = Boolean(user && (isAdmin || user.id === event.organizer));
  const canApproveEvent = Boolean(isAdmin && !event.is_approved);

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      <div className="relative h-[400px] w-full overflow-hidden">
        {event.image ? (
          <img src={event.image} alt={event.title} className="w-full h-full object-cover" />
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
              {!event.is_approved && (
                <span className="bg-amber-400 text-amber-950 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
                  Pending Approval
                </span>
              )}
            </div>
            <h1 className="text-4xl md:text-5xl font-extrabold text-white mb-4">{event.title}</h1>
            {canManageEvent && (
              <div className="flex flex-wrap gap-3">
                <Link
                  to={`/edit-event/${event.id}`}
                  className="inline-flex items-center gap-2 bg-white text-gray-900 px-4 py-2 rounded-xl font-semibold hover:bg-gray-100 transition-colors"
                >
                  <Edit3 className="w-4 h-4" />
                  Edit Event
                </Link>
                {canApproveEvent && (
                  <button
                    onClick={handleApprove}
                    disabled={actionLoading}
                    className="inline-flex items-center gap-2 bg-emerald-500 text-white px-4 py-2 rounded-xl font-semibold hover:bg-emerald-600 transition-colors disabled:opacity-60"
                  >
                    {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                    Approve Event
                  </button>
                )}
                <button
                  onClick={handleDelete}
                  disabled={actionLoading}
                  className="inline-flex items-center gap-2 bg-red-500 text-white px-4 py-2 rounded-xl font-semibold hover:bg-red-600 transition-colors disabled:opacity-60"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete Event
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-12">
        {notice && (
          <div className="mb-6 rounded-2xl border border-emerald-100 bg-emerald-50 px-5 py-4 text-sm font-medium text-emerald-700">
            {notice}
          </div>
        )}

        {actionError && (
          <div className="mb-6 rounded-2xl border border-red-100 bg-red-50 px-5 py-4 text-sm font-medium text-red-700">
            {actionError}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-2xl p-8 shadow-sm border border-gray-100">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">About this event</h2>
              <div className="prose prose-indigo max-w-none text-gray-600 leading-relaxed">
                {event.description.split('\n').map((paragraph, index) => (
                  <p key={index} className="mb-4">{paragraph}</p>
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
                    {event.organizer_email && (
                      <p className="text-gray-400 text-xs mt-2">Hosted by {event.organizer_email}</p>
                    )}
                  </div>
                </div>
              </div>

              {(event.parking_info || googleMapsLink || (event.latitude && event.longitude)) && (
                <div className="mt-10 pt-10 border-t border-gray-100">
                  <div className="flex items-start gap-4 mb-5">
                    <div className="bg-indigo-50 p-3 rounded-xl text-indigo-600">
                      <CarFront className="w-6 h-6" />
                    </div>
                    <div>
                      <h4 className="font-bold text-gray-900">Parking & Navigation</h4>
                      <p className="text-gray-600 text-sm mt-1">
                        {event.parking_info || 'Use the venue map below for easier arrival and parking access.'}
                      </p>
                    </div>
                  </div>

                  {(event.latitude && event.longitude) && (
                    <div className="mb-5">
                      <EventLocationMap latitude={Number(event.latitude)} longitude={Number(event.longitude)} />
                    </div>
                  )}

                  <div className="flex flex-wrap gap-4">
                    {googleMapsLink && (
                      <a
                        href={googleMapsLink}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-2 text-indigo-600 font-semibold hover:underline"
                      >
                        <Navigation className="w-4 h-4" />
                        Open in Google Maps
                      </a>
                    )}

                    {event.latitude && event.longitude && (
                      <a
                        href={`https://www.google.com/maps?q=${event.latitude},${event.longitude}`}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-2 text-indigo-600 font-semibold hover:underline"
                      >
                        <Navigation className="w-4 h-4" />
                        Open coordinates in map
                      </a>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 sticky top-24">
              <div className="flex items-center justify-between mb-6">
                <span className="text-gray-500 font-medium">Ticket Price</span>
                <span className="text-3xl font-bold text-indigo-600">
                  {formatNpr(event.price, { allowFree: true })}
                </span>
              </div>

              <div className="space-y-4 mb-8">
                <div className="flex items-center text-sm text-gray-600 gap-2">
                  <Users className="w-4 h-4 text-indigo-500" />
                  <span>
                    {event.remaining_capacity} left out of {event.capacity} total
                  </span>
                </div>
                <div className="flex items-center text-sm text-gray-600 gap-2">
                  <CheckCircle2 className="w-4 h-4 text-indigo-500" />
                  <span>{event.confirmed_booking_count} confirmed bookings</span>
                </div>
                <div className="flex items-center text-sm text-gray-600 gap-2">
                  <CheckCircle2 className="w-4 h-4 text-indigo-500" />
                  <span>Booking confirms automatically after successful payment</span>
                </div>
              </div>

              {user ? (
                <button
                  onClick={handleBooking}
                  disabled={bookingLoading || event.is_sold_out || !event.is_approved}
                  className="w-full bg-indigo-600 text-white font-bold py-4 rounded-xl hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {bookingLoading && <Loader2 className="w-5 h-5 animate-spin" />}
                  {bookingLoading
                    ? 'Starting checkout...'
                    : !event.is_approved
                      ? 'Awaiting Approval'
                      : event.is_sold_out
                        ? 'Sold Out'
                        : 'Book Now'}
                </button>
              ) : (
                <Link
                  to="/login"
                  state={{ from: { pathname: `/events/${id}` } }}
                  className={`block w-full text-center bg-gray-900 text-white font-bold py-4 rounded-xl hover:bg-gray-800 transition-all shadow-lg active:scale-[0.98] ${event.is_sold_out ? 'pointer-events-none opacity-50' : ''}`}
                >
                  {event.is_sold_out ? 'Sold Out' : 'Login to Book'}
                </Link>
              )}

              <p className="text-center text-xs text-gray-400 mt-6 px-4">
                Final payment amount in NRs, including any approved student discount, is shown during checkout.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


export default EventDetail;
