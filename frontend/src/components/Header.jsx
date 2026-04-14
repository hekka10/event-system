import { Link, useNavigate } from 'react-router-dom';
import { LogOut, User, Calendar, PlusSquare, LayoutDashboard, Ticket, BadgeCheck } from 'lucide-react';

import useAuth from '../hooks/useAuth';
import authService from '../services/authService';

function Header() {
  const navigate = useNavigate();
  const { user, isAdmin } = useAuth();

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  return (
    <header className="bg-white border-b border-gray-100 sticky top-0 z-50 backdrop-blur-md bg-white/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2">
              <div className="bg-indigo-600 p-1.5 rounded-lg">
                <Calendar className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600">
                SmartEvents
              </span>
            </Link>

            <nav className="hidden md:flex items-center gap-6">
              <Link to="/" className="text-sm font-medium text-gray-600 hover:text-indigo-600 transition-colors">Home</Link>
              <Link to="/events" className="text-sm font-medium text-gray-600 hover:text-indigo-600 transition-colors">Events</Link>
              {user && (
                <>
                  <Link to="/my-bookings" className="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-indigo-600 transition-colors">
                    <Ticket className="w-4 h-4" />
                    My Bookings
                  </Link>
                  {isAdmin && (
                    <Link to="/admin-dashboard" className="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-indigo-600 transition-colors">
                      <LayoutDashboard className="w-4 h-4" />
                      Dashboard
                    </Link>
                  )}
                  <Link to="/create-event" className="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-indigo-600 transition-colors">
                    <PlusSquare className="w-4 h-4" />
                    Create Event
                  </Link>
                  <Link to="/student-verification" className="flex items-center gap-1.5 text-sm font-medium text-gray-600 hover:text-indigo-600 transition-colors">
                    <BadgeCheck className="w-4 h-4" />
                    Student Verification
                  </Link>
                </>
              )}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            {user ? (
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-full border border-gray-100">
                  <div className="w-6 h-6 bg-indigo-100 rounded-full flex items-center justify-center text-indigo-600">
                    <User className="w-4 h-4" />
                  </div>
                  <span className="text-sm font-medium text-gray-700">{user.username || user.email.split('@')[0]}</span>
                  {user.is_student_verified && (
                    <span className="text-[10px] uppercase tracking-wide font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
                      Student
                    </span>
                  )}
                </div>
                <button
                  onClick={handleLogout}
                  className="p-2 text-gray-400 hover:text-red-500 transition-colors hover:bg-red-50 rounded-full"
                  title="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3">
                <Link to="/login" className="text-sm font-medium text-gray-600 hover:text-indigo-600 px-4 py-2 transition-colors">
                  Login
                </Link>
                <Link to="/signup" className="text-sm font-medium bg-indigo-600 text-white px-5 py-2.5 rounded-xl hover:bg-indigo-700 transition-all shadow-sm hover:shadow-indigo-100">
                  Sign Up
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
