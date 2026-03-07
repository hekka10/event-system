import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import eventService from '../services/eventService';
import EventCard from '../components/EventCard';
import { Sparkles, Calendar, Users, ShieldCheck, ArrowRight, Zap, Loader2 } from 'lucide-react';

function Home() {
  const [featuredEvents, setFeaturedEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLatestEvents = async () => {
      try {
        const data = await eventService.getAllEvents();
        setFeaturedEvents(data.slice(0, 3));
      } catch (err) {
        console.error('Error fetching latest events:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchLatestEvents();
  }, []);

  return (
    <div className="bg-white">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-indigo-50/50 to-white pt-20 pb-20 md:pt-32 md:pb-32">
        {/* Animated Blobs */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full pointer-events-none">
          <div className="absolute top-[10%] left-[10%] w-72 h-72 bg-indigo-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
          <div className="absolute top-[10%] right-[10%] w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse duration-3000"></div>
          <div className="absolute bottom-[20%] left-[20%] w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse duration-5000"></div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-600 text-sm font-bold mb-8 transition-all">
              <Zap className="w-4 h-4 fill-current" />
              Next Generation Event Management
            </div>
            <h1 className="text-5xl md:text-7xl font-extrabold text-gray-900 tracking-tight leading-[1.1] mb-8">
              Make Every Event <br />
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 via-violet-600 to-purple-600">
                Memorable & Seamless
              </span>
            </h1>
            <p className="max-w-2xl mx-auto text-xl text-gray-500 mb-10 leading-relaxed">
              From ticketing to check-ins, managed entirely with the Smart Event system. Focus on the experience, let us handle the logistics.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link to="/events" className="w-full sm:w-auto px-8 py-4 bg-indigo-600 text-white font-bold rounded-2xl hover:bg-indigo-700 transition-all shadow-xl shadow-indigo-200 flex items-center justify-center gap-2">
                Explore Events
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link to="/signup" className="w-full sm:w-auto px-8 py-4 bg-white text-gray-900 font-bold rounded-2xl border border-gray-200 hover:bg-gray-50 transition-all">
                Get Started for Free
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="p-8 rounded-3xl bg-gray-50 hover:bg-white border border-transparent hover:border-indigo-100 transition-all group">
              <div className="bg-white w-14 h-14 rounded-2xl flex items-center justify-center shadow-sm mb-6 group-hover:scale-110 transition-transform">
                <Calendar className="w-7 h-7 text-indigo-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Easy Scheduling</h3>
              <p className="text-gray-500 leading-relaxed">Create and manage multiple events with our intuitive dashboard in just a few clicks.</p>
            </div>
            <div className="p-8 rounded-3xl bg-gray-50 hover:bg-white border border-transparent hover:border-indigo-100 transition-all group">
              <div className="bg-white w-14 h-14 rounded-2xl flex items-center justify-center shadow-sm mb-6 group-hover:scale-110 transition-transform">
                <Users className="w-7 h-7 text-indigo-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Smart Check-ins</h3>
              <p className="text-gray-500 leading-relaxed">Fast check-ins with QR ticket scanning and real-time attendee management.</p>
            </div>
            <div className="p-8 rounded-3xl bg-gray-50 hover:bg-white border border-transparent hover:border-indigo-100 transition-all group">
              <div className="bg-white w-14 h-14 rounded-2xl flex items-center justify-center shadow-sm mb-6 group-hover:scale-110 transition-transform">
                <ShieldCheck className="w-7 h-7 text-indigo-600" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">Verified Bookings</h3>
              <p className="text-gray-500 leading-relaxed">Secure payment processing and automatic student verification for discounts.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Latest Events Section */}
      <section className="py-24 bg-gray-50/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-12">
            <div>
              <h2 className="text-3xl font-extrabold text-gray-900">Upcoming Events</h2>
              <p className="text-gray-500 font-medium mt-1">Don't miss out on these amazing experiences</p>
            </div>
            <Link to="/events" className="hidden sm:flex items-center gap-2 text-indigo-600 font-bold hover:text-indigo-700">
              See All
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {loading ? (
            <div className="flex justify-center py-20">
              <Loader2 className="w-12 h-12 text-indigo-600 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {featuredEvents.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
              {featuredEvents.length === 0 && (
                <div className="col-span-full text-center py-10 text-gray-500 font-medium">
                  No upcoming events at the moment.
                </div>
              )}
            </div>
          )}

          <div className="mt-12 text-center sm:hidden">
            <Link to="/events" className="inline-flex items-center gap-2 text-indigo-600 font-bold border-2 border-indigo-600 px-6 py-3 rounded-xl hover:bg-indigo-50 transition-all">
              View More Events
            </Link>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-indigo-600 rounded-[3rem] p-12 md:p-24 relative overflow-hidden shadow-2xl shadow-indigo-200">
            <div className="absolute top-0 right-0 -translate-y-12 translate-x-12 w-96 h-96 bg-white/10 rounded-full blur-3xl"></div>
            <div className="relative z-10 max-w-2xl">
              <h2 className="text-4xl md:text-5xl font-extrabold text-white mb-8">Ready to host your own event?</h2>
              <p className="text-indigo-100 text-xl mb-10 leading-relaxed">Join thousands of organizers using SmartEvents to simplify their planning and grow their audience.</p>
              <Link to="/signup" className="inline-flex bg-white text-indigo-600 font-bold px-10 py-5 rounded-2xl hover:bg-gray-50 transition-all shadow-xl shadow-indigo-900/10 active:scale-[0.98]">
                Start Hosting Now
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;