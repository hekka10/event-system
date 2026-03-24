import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar,
  CheckCircle2,
  Clock,
  DollarSign,
  GraduationCap,
  Loader2,
  ShoppingCart,
  Ticket,
  TrendingUp,
  Users,
} from 'lucide-react';

import OfflineBookingForm from '../components/OfflineBookingForm';
import TicketScannerPanel from '../components/TicketScannerPanel';
import authService from '../services/authService';
import adminService from '../services/adminService';
import eventService from '../services/eventService';
import studentService from '../services/studentService';


function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const user = authService.getCurrentUser();
  const token = user?.access || user?.token || '';
  const navigate = useNavigate();

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }

    const loadStats = async () => {
      setLoading(true);
      try {
        const data = await adminService.getStats(token);
        setStats(data);
        setError(null);
      } catch (statsError) {
        setError(statsError.message || 'Failed to load dashboard statistics.');
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, [token]);

  const fetchStats = async () => {
    if (!token) {
      return;
    }

    setLoading(true);
    try {
      const data = await adminService.getStats(token);
      setStats(data);
      setError(null);
    } catch (statsError) {
      setError(statsError.message || 'Failed to load dashboard statistics.');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveEvent = async (eventId) => {
    try {
      await eventService.approveEvent(eventId, token);
      fetchStats();
    } catch (approveError) {
      setError(approveError.message || 'Failed to approve event.');
    }
  };

  const handleReviewVerification = async (verificationId, status) => {
    try {
      await studentService.reviewVerification(
        verificationId,
        {
          status,
          rejection_reason: status === 'REJECTED' ? 'Please provide a valid student document.' : '',
        },
        token
      );
      fetchStats();
    } catch (reviewError) {
      setError(reviewError.message || 'Failed to review student verification.');
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
    { label: 'Checked In', value: stats.total_checked_in, icon: Ticket, color: 'bg-amber-500' },
    {
      label: 'Pending Student Reviews',
      value: stats.pending_student_verification_count,
      icon: GraduationCap,
      color: 'bg-rose-500',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-10">
          <h1 className="text-3xl font-extrabold text-gray-900">Admin Dashboard</h1>
          <p className="mt-2 text-gray-500 font-medium">Overview of your event operations, payments, and check-ins.</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-600 p-6 rounded-2xl text-center mb-8">
            <p>{error}</p>
            <button onClick={fetchStats} className="mt-2 font-bold underline">Try again</button>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6 mb-12">
          {statCards.map((stat) => (
            <div key={stat.label} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center gap-5">
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
          <div className="lg:col-span-2 space-y-8">
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="p-6 border-b border-gray-50 flex items-center justify-between bg-amber-50/30">
                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-amber-500" />
                  Pending Event Approvals
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
                        <td colSpan="3" className="px-6 py-10 text-center text-gray-500 italic">No pending event approvals.</td>
                      </tr>
                    ) : (
                      stats.pending_events.map((event) => (
                        <tr key={event.id} className="hover:bg-gray-50/50 transition-colors">
                          <td className="px-6 py-4 text-sm font-semibold text-gray-900">{event.title}</td>
                          <td className="px-6 py-4 text-sm text-gray-500">{event.organizer}</td>
                          <td className="px-6 py-4 text-right">
                            <button
                              onClick={() => handleApproveEvent(event.id)}
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

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="p-6 border-b border-gray-50 flex items-center justify-between bg-rose-50/40">
                <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <GraduationCap className="w-5 h-5 text-rose-500" />
                  Student Verification Queue
                </h3>
                <span className="px-2.5 py-1 bg-rose-100 text-rose-700 text-xs font-bold rounded-full">
                  {stats.pending_student_verifications.length} Pending
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="bg-gray-50/50">
                      <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">User</th>
                      <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider">Institution</th>
                      <th className="px-6 py-4 text-xs font-bold text-gray-400 uppercase tracking-wider text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-50">
                    {stats.pending_student_verifications.length === 0 ? (
                      <tr>
                        <td colSpan="3" className="px-6 py-10 text-center text-gray-500 italic">No student verifications waiting for review.</td>
                      </tr>
                    ) : (
                      stats.pending_student_verifications.map((verification) => (
                        <tr key={verification.id} className="hover:bg-gray-50/50 transition-colors">
                          <td className="px-6 py-4 text-sm">
                            <p className="font-semibold text-gray-900">{verification.user}</p>
                            <p className="text-gray-500">{verification.student_email}</p>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-600">{verification.institution_name}</td>
                          <td className="px-6 py-4 text-right space-x-2">
                            <button
                              onClick={() => handleReviewVerification(verification.id, 'APPROVED')}
                              className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold px-4 py-2 rounded-lg transition-all"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleReviewVerification(verification.id, 'REJECTED')}
                              className="bg-gray-900 hover:bg-gray-800 text-white text-xs font-bold px-4 py-2 rounded-lg transition-all"
                            >
                              Reject
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-6 border-b border-gray-50">
                  <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                    <ShoppingCart className="w-5 h-5 text-indigo-500" />
                    Recent Payments
                  </h3>
                </div>
                <div className="divide-y divide-gray-50">
                  {stats.recent_payments.length === 0 ? (
                    <p className="p-6 text-sm text-gray-500">No payments recorded yet.</p>
                  ) : (
                    stats.recent_payments.map((payment) => (
                      <div key={payment.id} className="p-6 flex items-center justify-between">
                        <div>
                          <p className="font-semibold text-gray-900">{payment.user}</p>
                          <p className="text-sm text-gray-500">{payment.reference}</p>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-indigo-600">${payment.amount}</p>
                          <p className="text-xs uppercase tracking-wide text-gray-400">{payment.status}</p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div className="p-6 border-b border-gray-50">
                  <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                    Recent Check-ins
                  </h3>
                </div>
                <div className="divide-y divide-gray-50">
                  {stats.recent_check_ins.length === 0 ? (
                    <p className="p-6 text-sm text-gray-500">No attendees checked in yet.</p>
                  ) : (
                    stats.recent_check_ins.map((checkIn) => (
                      <div key={checkIn.ticket_code} className="p-6">
                        <p className="font-semibold text-gray-900">{checkIn.attendee}</p>
                        <p className="text-sm text-gray-500">{checkIn.event}</p>
                        <p className="text-xs uppercase tracking-wide text-gray-400 mt-1">{checkIn.ticket_code}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-indigo-600 rounded-2xl p-6 text-white shadow-xl shadow-indigo-100 relative overflow-hidden">
              <TrendingUp className="w-24 h-24 absolute -right-4 -bottom-4 text-white/10" />
              <h3 className="text-lg font-bold mb-2">Operations Snapshot</h3>
              <p className="text-white/80 text-sm mb-6 leading-relaxed">
                Approvals, walk-ins, payments, and ticket scans are all connected from this dashboard now.
              </p>
              <button
                onClick={() => navigate('/events')}
                className="bg-white text-indigo-600 px-4 py-2 rounded-xl text-sm font-bold hover:bg-gray-50 transition-all"
              >
                Open Events
              </button>
            </div>

            <TicketScannerPanel onSuccess={fetchStats} />
            <OfflineBookingForm onSuccess={fetchStats} />
          </div>
        </div>
      </div>
    </div>
  );
}


export default AdminDashboard;
