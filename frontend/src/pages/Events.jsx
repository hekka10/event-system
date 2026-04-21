import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import AlertMessage from '../components/AlertMessage';
import eventService from '../services/eventService';
import EventCard from '../components/EventCard';
import { Filter, Loader2, Search, Sparkles, X } from 'lucide-react';
import useAuth from '../hooks/useAuth';

function Events() {
  const [events, setEvents] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState('');
  const { user, token } = useAuth();
  const location = useLocation();
  const normalizedSearchTerm = searchTerm.trim().toLowerCase();

  const filteredEvents = events.filter((event) => {
    if (!normalizedSearchTerm) {
      return true;
    }

    const searchableFields = [
      event.title,
      event.location,
      event.category_name,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();

    return searchableFields.includes(normalizedSearchTerm);
  });

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
        const data = await eventService.getAllEvents(selectedCategory, token || '');
        setEvents(data);
        setError(null);
      } catch {
        setError('Failed to load events. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    loadEvents();
  }, [selectedCategory, token]);

  const fetchEvents = async () => {
    setLoading(true);
    try {
      const data = await eventService.getAllEvents(selectedCategory, token || '');
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
          <AlertMessage variant="success" className="mb-8 font-medium">
            {notice}
          </AlertMessage>
        )}

        {/* Filters Section */}
        <div className="mb-10 space-y-4">
          <div className="mx-auto flex max-w-2xl items-center rounded-2xl border border-gray-200 bg-white px-4 py-3 shadow-sm">
            <Search className="mr-3 h-5 w-5 text-gray-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(event) => setSearchTerm(event.target.value)}
              placeholder="Search events by name, location, or category"
              className="w-full bg-transparent text-sm font-medium text-gray-700 outline-none placeholder:text-gray-400"
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm('')}
                className="ml-3 rounded-full p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600"
                aria-label="Clear search"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          <div className="flex flex-wrap items-center justify-center gap-4">
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

            {(selectedCategory || searchTerm) && (
              <button
                type="button"
                onClick={() => {
                  setSelectedCategory('');
                  setSearchTerm('');
                }}
                className="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-600 shadow-sm transition-colors hover:border-indigo-300 hover:text-indigo-600"
              >
                Clear search and filters
              </button>
            )}
          </div>

          <div className="text-center text-sm font-medium text-gray-500">
            Showing {filteredEvents.length} of {events.length} events
          </div>
        </div>

        {/* Content Section */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mb-4" />
            <p className="text-gray-500 font-medium">Loading events...</p>
          </div>
        ) : error ? (
          <AlertMessage
            variant="error"
            centered
            className="rounded-xl p-8"
            actions={(
              <button
                onClick={fetchEvents}
                className="font-semibold text-indigo-600 underline hover:text-indigo-700"
              >
                Try again
              </button>
            )}
          >
            <p className="font-medium">{error}</p>
          </AlertMessage>
        ) : filteredEvents.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
            {filteredEvents.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        ) : (
          <div className="text-center py-20 bg-white rounded-2xl border border-dashed border-gray-300">
            <p className="text-gray-500 text-lg">
              {searchTerm
                ? `No events match "${searchTerm}".`
                : 'No events found in this category.'}
            </p>
            <button
              onClick={() => {
                setSelectedCategory('');
                setSearchTerm('');
              }}
              className="mt-2 text-indigo-600 font-semibold hover:text-indigo-700"
            >
              Clear search and filters
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default Events;
