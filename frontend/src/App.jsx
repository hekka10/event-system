import { useEffect } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import AdminRoute from './components/AdminRoute';
import Footer from './components/Footer';
import Header from './components/Header';
import ProtectedRoute from './components/ProtectedRoute';
import useAuth from './hooks/useAuth';
import authService from './services/authService';
import AdminDashboard from './pages/AdminDashboard';
import AdminOfflineBooking from './pages/AdminOfflineBooking';
import EventDetail from './pages/EventDetail';
import EventForm from './pages/EventForm';
import Events from './pages/Events';
import ForgotPassword from './pages/ForgotPassword';
import Home from './pages/Home';
import Login from './pages/Login';
import MyBookings from './pages/MyBookings';
import PaymentCheckout from './pages/PaymentCheckout';
import ResetPassword from './pages/ResetPassword';
import Signup from './pages/Signup';
import StudentVerification from './pages/StudentVerification';


function App() {
  const { isAuthenticated, token, isAdmin } = useAuth();

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    authService.refreshProfile(token).catch(() => {
      authService.logout();
    });
  }, [isAuthenticated, token]);

  return (
    <BrowserRouter>
      <Header />
      <main className="min-h-screen">
        <Routes>
          <Route
            path="/"
            element={isAdmin ? <Navigate to="/admin-dashboard" replace /> : <Home />}
          />
          <Route path="/events" element={<Events />} />
          <Route path="/events/:id" element={<EventDetail />} />
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password/:uid/:token" element={<ResetPassword />} />
          <Route path="/signup" element={<Signup />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/my-bookings" element={<MyBookings />} />
            <Route path="/create-event" element={<EventForm />} />
            <Route path="/edit-event/:id" element={<EventForm />} />
            <Route path="/checkout/:paymentId" element={<PaymentCheckout />} />
            <Route path="/student-verification" element={<StudentVerification />} />
          </Route>

          <Route element={<AdminRoute />}>
            <Route path="/admin-dashboard" element={<AdminDashboard />} />
            <Route path="/admin/offline-booking" element={<AdminOfflineBooking />} />
          </Route>
        </Routes>
      </main>
      <Footer />
    </BrowserRouter>
  );
}


export default App;
