import { ArrowRight, Loader2, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import EventCard from './EventCard';

function RecommendedEventsSection({ events, loading }) {
  return (
    <section className="py-24 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-12">
          <div>
            <h2 className="text-3xl font-extrabold text-gray-900 flex items-center gap-3">
              <Sparkles className="w-8 h-8 text-indigo-600" />
              Recommended for You
            </h2>
            <p className="text-gray-500 font-medium mt-2">
              Suggestions based on the categories from events you attended before.
            </p>
          </div>
          <Link to="/events" className="hidden sm:flex items-center gap-2 text-indigo-600 font-bold hover:text-indigo-700">
            Browse All
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-12 h-12 text-indigo-600 animate-spin" />
          </div>
        ) : events.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {events.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        ) : (
          <div className="rounded-3xl border border-dashed border-gray-300 bg-gray-50/50 p-12 text-center">
            <p className="text-lg font-medium text-gray-700">No recommendations yet.</p>
            <p className="mt-2 text-gray-500">
              Book a few events and we will tailor this section to your interests.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}

export default RecommendedEventsSection;
