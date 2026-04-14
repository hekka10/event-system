import { Calendar, Mail, Github, Twitter, Instagram } from 'lucide-react';
import { Link } from 'react-router-dom';
import useAuth from '../hooks/useAuth';

function Footer() {
  const { user, isAdmin } = useAuth();

  return (
    <footer className="bg-white border-t border-gray-100 pt-16 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
          {/* Brand */}
          <div className="col-span-1 md:col-span-1">
            <Link to="/" className="flex items-center gap-2 mb-6">
              <div className="bg-indigo-600 p-1.5 rounded-lg">
                <Calendar className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600">
                SmartEvents
              </span>
            </Link>
            <p className="text-gray-500 text-sm leading-relaxed mb-6">
              Empowering students and organizers to create and discover incredible campus experiences with ease.
            </p>
            <div className="flex items-center gap-4">
              <a href="#" className="p-2 bg-gray-50 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-all">
                <Twitter className="w-5 h-5" />
              </a>
              <a href="#" className="p-2 bg-gray-50 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-all">
                <Instagram className="w-5 h-5" />
              </a>
              <a href="#" className="p-2 bg-gray-50 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-all">
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Links */}
          <div>
            <h4 className="font-bold text-gray-900 mb-6">Platform</h4>
            <ul className="space-y-4">
              <li><Link to="/events" className="text-gray-500 hover:text-indigo-600 text-sm transition-colors">Browse Events</Link></li>
              {user ? (
                <>
                  <li><Link to="/create-event" className="text-gray-500 hover:text-indigo-600 text-sm transition-colors">Host an Event</Link></li>
                  <li><Link to="/my-bookings" className="text-gray-500 hover:text-indigo-600 text-sm transition-colors">My Tickets</Link></li>
                  <li><Link to="/student-verification" className="text-gray-500 hover:text-indigo-600 text-sm transition-colors">Student Verification</Link></li>
                  {isAdmin && (
                    <li><Link to="/admin-dashboard" className="text-gray-500 hover:text-indigo-600 text-sm transition-colors">Admin Dashboard</Link></li>
                  )}
                </>
              ) : (
                <li><Link to="/login" className="text-gray-500 hover:text-indigo-600 text-sm transition-colors">Login to Manage</Link></li>
              )}
            </ul>
          </div>

          <div>
            <h4 className="font-bold text-gray-900 mb-6">Support</h4>
            <ul className="space-y-4">
              <li><a href="#" className="text-gray-500 hover:text-indigo-600 text-sm transition-colors">Help Center</a></li>
              <li><a href="#" className="text-gray-500 hover:text-indigo-600 text-sm transition-colors">Safety Center</a></li>
              <li><a href="#" className="text-gray-500 hover:text-indigo-600 text-sm transition-colors">Community Guidelines</a></li>
            </ul>
          </div>

          {/* Newsletter */}
          <div>
            <h4 className="font-bold text-gray-900 mb-6">Stay Updated</h4>
            <p className="text-gray-500 text-sm mb-4">Get the latest event updates delivered to your inbox.</p>
            <div className="relative">
              <input
                type="email"
                placeholder="Enter your email"
                className="w-full pl-4 pr-12 py-3 bg-gray-50 border border-gray-100 rounded-xl focus:ring-2 focus:ring-indigo-600 outline-none text-sm transition-all"
              />
              <button className="absolute right-2 top-1/2 -translate-y-1/2 bg-indigo-600 text-white p-1.5 rounded-lg hover:bg-indigo-700 transition-all">
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>

        <div className="pt-8 border-t border-gray-50 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-gray-400 text-xs">
            © 2026 SmartEvents. All rights reserved.
          </p>
          <div className="flex gap-8">
            <a href="#" className="text-gray-400 hover:text-gray-600 text-xs transition-colors">Privacy Policy</a>
            <a href="#" className="text-gray-400 hover:text-gray-600 text-xs transition-colors">Terms of Service</a>
            <a href="#" className="text-gray-400 hover:text-gray-600 text-xs transition-colors">Cookie Settings</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

const ArrowRight = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14m-7-7 7 7-7 7" /></svg>
)

export default Footer;
