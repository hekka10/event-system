import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, CreditCard, ExternalLink, Loader2, ShieldCheck, XCircle } from 'lucide-react';

import bookingService from '../services/bookingService';
import useAuth from '../hooks/useAuth';
import { formatNpr } from '../utils/currency';


function PaymentCheckout() {
  const { paymentId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { token } = useAuth();
  const esewaFormRef = useRef(null);

  const [payment, setPayment] = useState(null);
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [esewaRedirecting, setEsewaRedirecting] = useState(false);
  const [error, setError] = useState('');
  const queryParams = new URLSearchParams(location.search);
  const paymentGateway = queryParams.get('gateway');
  const paymentStatus = queryParams.get('status');

  const formatPrice = (value) => formatNpr(value);

  const notice = location.state?.message
    || (
      paymentGateway === 'esewa' && paymentStatus === 'success'
        ? 'eSewa payment verified successfully. Your booking is now confirmed.'
        : ''
    );
  const callbackError = paymentGateway === 'esewa' && paymentStatus === 'failed'
    ? 'eSewa payment was not completed. You can start a new payment from the event page.'
    : '';

  useEffect(() => {
    if (!token) {
      navigate('/login', { replace: true });
      return;
    }

    const fetchPayment = async () => {
      try {
        const data = await bookingService.getPayment(paymentId, token);
        setPayment(data.payment);
        setBooking(data.booking);
      } catch (fetchError) {
        setError(fetchError.message || 'Failed to load checkout details.');
      } finally {
        setLoading(false);
      }
    };

    fetchPayment();
  }, [location.search, navigate, paymentId, token]);

  const handleVerification = async (status) => {
    setActionLoading(true);
    setError('');

    try {
      const data = await bookingService.verifyPayment(
        paymentId,
        {
          status,
          provider_reference: `SANDBOX-${paymentId.slice(0, 8).toUpperCase()}`,
          provider_response: {
            gateway: 'sandbox',
            confirmed_by_user: true,
          },
        },
        token
      );

      setPayment(data.payment);
      setBooking(data.booking);

      if (status === 'SUCCESS') {
        navigate('/my-bookings', {
          state: { message: 'Payment successful. Your booking is confirmed.' },
        });
      }
    } catch (verifyError) {
      setError(verifyError.message || 'Failed to complete payment.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEsewaSubmit = () => {
    if (!payment?.checkout_url || !payment?.form_fields || !esewaFormRef.current) {
      setError('eSewa checkout details are incomplete. Please try again.');
      return;
    }

    setEsewaRedirecting(true);
    esewaFormRef.current?.submit();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
      </div>
    );
  }

  if (error && !payment) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="bg-white p-8 rounded-2xl border border-gray-100 max-w-md text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <Link to="/my-bookings" className="text-indigo-600 font-semibold hover:underline">
            Go to My Bookings
          </Link>
        </div>
      </div>
    );
  }

  const isEsewaPayment = payment?.provider === 'ESEWA';
  const isSuccessful = payment?.status === 'SUCCESS';
  const isFinalized = payment?.status === 'SUCCESS' || payment?.status === 'FAILED';
  const eventId = booking?.event_details?.id;
  const gatewayDescription = isEsewaPayment
    ? 'You will be redirected to eSewa to complete payment securely.'
    : `Sandbox checkout for ${booking?.event_details?.title}`;

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <Link to="/events" className="inline-flex items-center gap-2 text-gray-500 hover:text-indigo-600 mb-6">
          <ArrowLeft className="w-4 h-4" />
          Back to events
        </Link>

        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-8 border-b border-gray-100 bg-gray-50/70">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-indigo-600 p-3 rounded-2xl text-white">
                <CreditCard className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Complete Your Payment</h1>
                <p className="text-sm text-gray-500">
                  {gatewayDescription}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="rounded-2xl bg-white p-4 border border-gray-100">
                <p className="text-xs uppercase tracking-wider text-gray-400 font-bold">Amount (NRs)</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{formatPrice(payment?.amount)}</p>
              </div>
              <div className="rounded-2xl bg-white p-4 border border-gray-100">
                <p className="text-xs uppercase tracking-wider text-gray-400 font-bold">Provider</p>
                <p className="text-lg font-bold text-gray-900 mt-1">{payment?.provider}</p>
              </div>
              <div className="rounded-2xl bg-white p-4 border border-gray-100">
                <p className="text-xs uppercase tracking-wider text-gray-400 font-bold">Status</p>
                <p className="text-lg font-bold text-gray-900 mt-1">{payment?.status}</p>
              </div>
            </div>

            {payment?.transaction_ref && (
              <div className="mt-4 rounded-2xl bg-white p-4 border border-gray-100">
                <p className="text-xs uppercase tracking-wider text-gray-400 font-bold">Transaction Ref</p>
                <p className="mt-1 font-mono text-sm font-semibold text-gray-900">{payment.transaction_ref}</p>
              </div>
            )}
          </div>

          <div className="p-8">
            {notice && (
              <div className="mb-6 bg-emerald-50 border border-emerald-100 text-emerald-700 p-4 rounded-2xl">
                {notice}
              </div>
            )}

            {callbackError && (
              <div className="mb-6 bg-red-50 border border-red-100 text-red-600 p-4 rounded-2xl">
                {callbackError}
              </div>
            )}

            {error && (
              <div className="mb-6 bg-red-50 border border-red-100 text-red-600 p-4 rounded-2xl">
                {error}
              </div>
            )}

            <div className="bg-indigo-50 border border-indigo-100 rounded-2xl p-6 mb-8">
              <div className="flex items-start gap-3">
                <ShieldCheck className="w-5 h-5 text-indigo-600 mt-0.5" />
                <div>
                  <h2 className="font-bold text-gray-900">
                    {isEsewaPayment ? 'eSewa Payment Gateway' : 'Sandbox Payment Gateway'}
                  </h2>
                  {isEsewaPayment ? (
                    <p className="text-sm text-gray-600 mt-1">
                      This payment will be completed on eSewa. After eSewa redirects back, the backend verifies
                      the transaction before confirming your booking and generating the QR ticket.
                    </p>
                  ) : (
                    <p className="text-sm text-gray-600 mt-1">
                      This checkout is wired end to end for payment initiation, verification, booking confirmation,
                      QR ticket generation, and email delivery. Replace the sandbox provider with a live gateway by
                      updating the backend payment service configuration.
                    </p>
                  )}
                </div>
              </div>
            </div>

            {isEsewaPayment && payment?.form_fields && payment?.checkout_url && (
              <form ref={esewaFormRef} action={payment.checkout_url} method="POST" className="hidden">
                {Object.entries(payment.form_fields).map(([field, value]) => (
                  <input
                    key={field}
                    type="hidden"
                    name={field}
                    value={value == null ? '' : String(value)}
                  />
                ))}
              </form>
            )}

            {booking && (
              <div className="mb-8 rounded-2xl border border-gray-100 bg-gray-50 p-6">
                <h2 className="text-lg font-bold text-gray-900 mb-4">Price Breakdown</h2>
                {booking.is_student && Number(booking.discount_amount) > 0 && (
                  <div className="mb-4 rounded-2xl border border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
                    Verified student discount applied to this payment.
                  </div>
                )}
                <div className="space-y-3 text-sm text-gray-600">
                  <div className="flex items-center justify-between">
                    <span>Base ticket price</span>
                    <span className="font-semibold text-gray-900">{formatPrice(booking.base_price)}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span>Student discount</span>
                    <span className="font-semibold text-emerald-600">-{formatPrice(booking.discount_amount)}</span>
                  </div>
                  <div className="flex items-center justify-between border-t border-gray-200 pt-3 text-base">
                    <span className="font-bold text-gray-900">Total due</span>
                    <span className="font-bold text-indigo-600">{formatPrice(booking.total_price)}</span>
                  </div>
                </div>
              </div>
            )}

            {isEsewaPayment ? (
              <div className="space-y-3">
                {!isFinalized && (
                  <div className="rounded-2xl border border-amber-100 bg-amber-50 px-4 py-3 text-sm text-amber-700">
                    Click Pay Now once to continue to eSewa and complete your booking payment.
                  </div>
                )}

                {!isFinalized && (
                  <button
                    type="button"
                    disabled={esewaRedirecting}
                    onClick={handleEsewaSubmit}
                    className="w-full bg-indigo-600 text-white font-bold py-4 rounded-2xl hover:bg-indigo-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                  >
                    {esewaRedirecting ? <Loader2 className="w-5 h-5 animate-spin" /> : <ExternalLink className="w-5 h-5" />}
                    {esewaRedirecting ? 'Opening eSewa...' : 'Pay Now'}
                  </button>
                )}

                {payment?.status === 'SUCCESS' && (
                  <Link
                    to="/my-bookings"
                    className="w-full bg-emerald-600 text-white font-bold py-4 rounded-2xl hover:bg-emerald-700 transition-all flex items-center justify-center gap-2"
                  >
                    <ShieldCheck className="w-5 h-5" />
                    View Confirmed Booking
                  </Link>
                )}

                {payment?.status === 'FAILED' && eventId && (
                  <Link
                    to={`/events/${eventId}`}
                    className="w-full bg-gray-100 text-gray-700 font-semibold py-4 rounded-2xl hover:bg-gray-200 transition-all flex items-center justify-center gap-2"
                  >
                    <ArrowLeft className="w-5 h-5" />
                    Back to Event
                  </Link>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                <button
                  type="button"
                  disabled={actionLoading || isSuccessful}
                  onClick={() => handleVerification('SUCCESS')}
                  className="w-full bg-indigo-600 text-white font-bold py-4 rounded-2xl hover:bg-indigo-700 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {actionLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <ShieldCheck className="w-5 h-5" />}
                  {isSuccessful ? 'Payment Completed' : 'Pay Now'}
                </button>

                <button
                  type="button"
                  disabled={actionLoading || isSuccessful}
                  onClick={() => handleVerification('FAILED')}
                  className="w-full bg-gray-100 text-gray-700 font-semibold py-4 rounded-2xl hover:bg-gray-200 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <XCircle className="w-5 h-5" />
                  Simulate Failed Payment
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


export default PaymentCheckout;
