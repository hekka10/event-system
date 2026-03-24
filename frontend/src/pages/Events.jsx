import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import eventService from '../services/eventService';
import EventCard from '../components/EventCard';
import { Filter, Loader2, Sparkles } from 'lucide-react';
import authService from '../services/authService';

function Events() {
  const [events, setEvents] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState('');
  const user = authService.getCurrentUser();
  const location = useLocation();

  useEffect(() => {
    setNotice(location.state?.message || '');
  }, [location.state]);

  useEffect(() => {
    const loadCategories = async () => {
      try {
        const data = await eventService.getCategories();
        setCategories(data);
      } catch (categoryError) {
        console.error('Error fetching categories:', categoryError);
      }
    };

    loadCategories();
  }, []);

  useEffect(() => {
    const loadEvents = async () => {
      setLoading(true);
      try {
        const data = await eventService.getAllEvents(selectedCategory, user?.access || user?.token || '');
        setEvents(data);
        setError(null);
      } catch {
        setError('Failed to load events. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    loadEvents();
  }, [selectedCategory, user?.access, user?.token]);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const data = await eventService.getAllEvents(selectedCategory, user?.access || user?.token || '');
      setEvents(data);
      setError(null);
    } catch {
      setError('Failed to load events. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl flex items-center justify-center gap-3">
            <Sparkles className="text-indigo-600 w-10 h-10" />
            Discover amazing events
          </h1>
          <p className="mt-4 text-xl text-gray-500 max-w-2xl mx-auto">
            Find the best workshops, conferences, and meetups happening near you.
          </p>
          {user && (
            <div className="mt-6 flex flex-col items-center gap-3">
              <Link
                to="/create-event"
                className="inline-flex items-center rounded-xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-100 transition-colors hover:bg-indigo-700"
              >
                Create Event
              </Link>
              <p className="text-sm text-gray-500">
                Your pending events stay visible to you while they wait for admin approval.
              </p>
            </div>
          )}
        </div>

        {notice && (
          <div className="mb-8 rounded-2xl border border-emerald-100 bg-emerald-50 px-5 py-4 text-sm font-medium text-emerald-700">
            {notice}
          </div>
        )}

        {/* Filters Section */}
        <div className="mb-10 flex flex-wrap items-center justify-center gap-4">
          <div className="flex items-center bg-white px-4 py-2 rounded-lg border border-gray-200 shadow-sm">
            <Filter className="w-5 h-5 text-gray-400 mr-2" />
            <span className="text-sm font-medium text-gray-700 mr-4">Filter by:</span>
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedCategory('')}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${selectedCategory === ''
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
              >
                All
              </button>
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${selectedCategory === cat.id
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                >
                  {cat.name}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Content Section */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mb-4" />
            <p className="text-gray-500 font-medium">Loading events...</p>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-xl p-8 text-center">
            <p className="text-red-600 font-medium">{error}</p>
            <button
              onClick={fetchEvents}
              className="mt-4 text-indigo-600 font-semibold hover:text-indigo-700 underline"
            >
              Try again
            </button>
          </div>
        ) : events.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        ) : (
          <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-gray-300">
            <p className="text-gray-500 text-lg">No events found in this category.</p>
            <button
              onClick={() => setSelectedCategory('')}
              className="mt-2 text-indigo-600 font-semibold hover:text-indigo-700"
            >
              Clear filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Events;
