import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import adminService from '../services/adminService';
import authService from '../services/authService';
import OfflineBookingForm from '../components/OfflineBookingForm';
import eventService from '../services/eventService';
import { Users, Calendar, ShoppingCart, DollarSign, ArrowUpRight, Loader2, TrendingUp, Clock } from 'lucide-react';


function AdminDashboard() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const user = authService.getCurrentUser();
    const navigate = useNavigate();

    useEffect(() => {
        // Basic check: in a real app, backend would return 403 if not admin
        if (!user) {
            navigate('/login');
            return;
        }
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            const data = await adminService.getStats(user.access || user.token);
            setStats(data);
        } catch (err) {
            setError('Failed to load dashboard statistics.');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
                <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mb-4" />
                <p className="text-gray-500 font-medium">Loading dashboard stats...</p>
            </div>
        );
    }

    const statCards = [
        { label: 'Total Users', value: stats.total_users, icon: Users, color: 'bg-blue-500' },
        { label: 'Total Events', value: stats.total_events, icon: Calendar, color: 'bg-indigo-500' },
        { label: 'Total Bookings', value: stats.total_bookings, icon: ShoppingCart, color: 'bg-violet-500' },
        { label: 'Total Revenue', value: `$${stats.total_revenue}`, icon: DollarSign, color: 'bg-emerald-500' },
    ];

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
                <div className="mb-10">
                    <h1 className="text-3xl font-extrabold text-gray-900">Admin Dashboard</h1>
                    <p className="mt-2 text-gray-500 font-medium">Overview of your event management system</p>
                </div>

                {error && (
                    <div className="bg-red-50 border border-red-200 text-red-600 p-6 rounded-2xl text-center mb-8">
                        <p>{error}</p>
                        <button onClick={fetchStats} className="mt-2 font-bold underline">Try again</button>
                    </div>
                )}

                {/* Stats Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                    {statCards.map((stat, i) => (
                        <div key={i} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-5">
                            <div className={`${stat.color} p-3 rounded-xl text-white shadow-lg`}>
                                <stat.icon className="w-6 h-6" />
                            </div>
                            <div>
                                <p className="text-sm font-medium text-gray-500">{stat.label}</p>
                                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Main Content Area */}
                    <div className="lg:col-span-2 space-y-8">
                        {/* Pending Approvals */}
                        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                            <div className="p-6 border-b border-gray-50 flex items-center justify-between bg-amber-50/30">
                                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                                    <Clock className="w-5 h-5 text-amber-500" />
                                    Pending Approvals
                                </h3>
                                <span className="px-2.5 py-1 bg-amber-100 text-amber-700 text-xs font-bold rounded-full">
                                    {stats.pending_events.length} Action Required
                                </span>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead>
                                        <tr className="bg-gray-50/50">
                                            <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Event Title</th>
                                            <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Organizer</th>
                                            <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-50">
                                        {stats.pending_events.length === 0 ? (
                                            <tr>
                                                <td colSpan="3" className="px-6 py-10 text-center text-gray-500 italic">No pending approvals at the moment.</td>
                                            </tr>
                                        ) : (
                                            stats.pending_events.map((event) => (
                                                <tr key={event.id} className="hover:bg-gray-50/50 transition-colors">
                                                    <td className="px-6 py-4 text-sm font-semibold text-gray-900">{event.title}</td>
                                                    <td className="px-6 py-4 text-sm text-gray-500">{event.organizer}</td>
                                                    <td className="px-6 py-4 text-right">
                                                        <button
                                                            onClick={async () => {
                                                                try {
                                                                    await eventService.approveEvent(event.id, user.access || user.token);
                                                                    fetchStats();
                                                                } catch (err) {
                                                                    alert('Failed to approve event');
                                                                }
                                                            }}
                                                            className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-4 py-2 rounded-lg transition-all"
                                                        >
                                                            Approve
                                                        </button>
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </div>

                        {/* Recent Activity Table */}
                        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                            <div className="p-6 border-b border-gray-50 flex items-center justify-between">
                                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                                    <ShoppingCart className="w-5 h-5 text-indigo-500" />
                                    Recent Bookings
                                </h3>
                                <button className="text-sm font-semibold text-indigo-600 hover:text-indigo-700">View all</button>
                            </div>
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead>
                                        <tr className="bg-gray-50/50">
                                            <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">User</th>
                                            <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Event</th>
                                            <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider text-right">Amount</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-gray-50">
                                        {stats.latest_bookings.map((booking) => (
                                            <tr key={booking.id} className="hover:bg-gray-50/50 transition-colors">
                                                <td className="px-6 py-4 text-sm font-medium text-gray-700 truncate max-w-[150px]">{booking.user}</td>
                                                <td className="px-6 py-4 text-sm text-gray-600 font-medium truncate max-w-[200px]">{booking.event}</td>
                                                <td className="px-6 py-4 text-sm font-bold text-indigo-600 text-right">${booking.amount}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    {/* Quick Actions / Insights */}
                    <div className="space-y-6">
                        <div className="bg-indigo-600 rounded-2xl p-6 text-white shadow-xl shadow-indigo-100 relative overflow-hidden">
                            <TrendingUp className="w-24 h-24 absolute -right-4 -bottom-4 text-white/10" />
                            <h3 className="text-lg font-bold mb-2">Growth Analytics</h3>
                            <p className="text-white/80 text-sm mb-6 leading-relaxed">System performance is optimal. You've seen a 12% increase in bookings this week.</p>
                            <button className="bg-white text-indigo-600 px-4 py-2 rounded-xl text-sm font-bold hover:bg-gray-50 transition-all flex items-center gap-2">
                                Check Details
                                <ArrowUpRight className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                            <h3 className="text-lg font-bold text-gray-900 mb-4">Quick Links</h3>
                            <div className="space-y-3">
                                <button
                                    onClick={() => navigate('/create-event')}
                                    className="w-full text-left px-4 py-3 bg-gray-50 rounded-xl text-sm font-medium text-gray-700 hover:bg-indigo-50 hover:text-indigo-600 transition-all"
                                >
                                    Create New Event
                                </button>
                                <button
                                    onClick={() => navigate('/events')}
                                    className="w-full text-left px-4 py-3 bg-gray-50 rounded-xl text-sm font-medium text-gray-700 hover:bg-indigo-50 hover:text-indigo-600 transition-all"
                                >
                                    Manage All Events
                                </button>
                            </div>
                        </div>

                        <OfflineBookingForm onSuccess={fetchStats} />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default AdminDashboard;
