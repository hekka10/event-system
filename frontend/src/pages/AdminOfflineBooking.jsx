import { Link } from 'react-router-dom';
import { ArrowLeft, ShieldCheck, Ticket, UserPlus } from 'lucide-react';

import OfflineBookingForm from '../components/OfflineBookingForm';


function AdminOfflineBooking() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <Link
              to="/admin-dashboard"
              className="inline-flex items-center gap-2 text-sm font-semibold text-indigo-600 hover:text-indigo-700 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back to Dashboard
            </Link>
            <h1 className="mt-3 text-3xl font-extrabold text-gray-900">Offline Booking Desk</h1>
            <p className="mt-2 text-gray-500 font-medium">
              Confirm walk-in attendees for approved events and generate tickets instantly.
            </p>
          </div>

          <div className="rounded-2xl border border-indigo-100 bg-indigo-50 px-5 py-4 text-sm text-indigo-700">
            This page is for admin-operated counter or event-day walk-in bookings.
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-2xl bg-white border border-gray-100 p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-indigo-100 p-3 text-indigo-600">
                <UserPlus className="w-5 h-5" />
              </div>
              <div>
                <p className="font-semibold text-gray-900">Walk-in Entry</p>
                <p className="text-sm text-gray-500">Create bookings for guests who arrive on site.</p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl bg-white border border-gray-100 p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-emerald-100 p-3 text-emerald-600">
                <Ticket className="w-5 h-5" />
              </div>
              <div>
                <p className="font-semibold text-gray-900">Instant Ticketing</p>
                <p className="text-sm text-gray-500">Tickets are generated as soon as the offline booking is confirmed.</p>
              </div>
            </div>
          </div>

          <div className="rounded-2xl bg-white border border-gray-100 p-5 shadow-sm">
            <div className="flex items-center gap-3">
              <div className="rounded-xl bg-amber-100 p-3 text-amber-600">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <p className="font-semibold text-gray-900">Admin Only</p>
                <p className="text-sm text-gray-500">This booking desk stays restricted to authorized admin users.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_320px] gap-8 items-start">
          <OfflineBookingForm />

          <div className="rounded-3xl bg-white border border-gray-100 p-6 shadow-sm space-y-5">
            <div>
              <h2 className="text-lg font-bold text-gray-900">How it works</h2>
              <p className="mt-2 text-sm text-gray-500 leading-relaxed">
                Choose an approved event, enter the attendee email, and confirm the walk-in booking.
                The system creates the attendee if needed, records the booking, and generates a ticket code.
              </p>
            </div>

            <div className="rounded-2xl bg-gray-50 border border-gray-100 p-4 text-sm text-gray-600">
              Use a real attendee email whenever possible so ticket emails and future reminders keep working.
            </div>

            <div className="space-y-3">
              <Link
                to="/admin-dashboard"
                className="inline-flex w-full items-center justify-center rounded-xl bg-gray-900 px-4 py-3 text-sm font-bold text-white hover:bg-gray-800 transition-all"
              >
                Open Dashboard
              </Link>
              <Link
                to="/events"
                className="inline-flex w-full items-center justify-center rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-all"
              >
                Browse Events
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


export default AdminOfflineBooking;
