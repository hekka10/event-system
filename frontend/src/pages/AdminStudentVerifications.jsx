import { useEffect, useState } from 'react';
import { BadgeCheck, FileText, Loader2, ShieldCheck, XCircle } from 'lucide-react';

import AlertMessage from '../components/AlertMessage';
import useAuth from '../hooks/useAuth';
import studentService from '../services/studentService';
import { formatDateTime } from '../utils/date';


const statusStyles = {
  APPROVED: 'bg-emerald-100 text-emerald-700',
  PENDING: 'bg-amber-100 text-amber-700',
  REJECTED: 'bg-rose-100 text-rose-700',
};

const filters = ['PENDING', 'APPROVED', 'REJECTED', 'ALL'];

function AdminStudentVerifications() {
  const { token } = useAuth();

  const [filter, setFilter] = useState('PENDING');
  const [verifications, setVerifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [savingId, setSavingId] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [rejectionReasons, setRejectionReasons] = useState({});

  useEffect(() => {
    const loadVerifications = async () => {
      if (!token) {
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const data = await studentService.getPendingVerifications(
          token,
          filter === 'ALL' ? '' : filter,
        );
        setVerifications(data);
        setError('');
      } catch (fetchError) {
        setError(fetchError.message || 'Failed to load student verification requests.');
      } finally {
        setLoading(false);
      }
    };

    loadVerifications();
  }, [filter, token]);

  const refreshVerifications = async (status = filter) => {
    if (!token) {
      return;
    }

    setLoading(true);
    try {
      const data = await studentService.getPendingVerifications(
        token,
        status === 'ALL' ? '' : status,
      );
      setVerifications(data);
      setError('');
    } catch (fetchError) {
      setError(fetchError.message || 'Failed to load student verification requests.');
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (verificationId, status) => {
    const rejectionReason = (rejectionReasons[verificationId] || '').trim();

    if (status === 'REJECTED' && !rejectionReason) {
      setError('Please add a rejection reason before rejecting a verification.');
      return;
    }

    setSavingId(verificationId);
    setError('');
    setSuccess('');

    try {
      await studentService.reviewVerification(
        verificationId,
        status === 'APPROVED'
          ? { status }
          : { status, rejection_reason: rejectionReason },
        token,
      );

      setSuccess(
        status === 'APPROVED'
          ? 'Student verification approved successfully.'
          : 'Student verification rejected successfully.',
      );
      setRejectionReasons((current) => ({ ...current, [verificationId]: '' }));
      await refreshVerifications(filter);
    } catch (reviewError) {
      setError(reviewError.message || 'Failed to review student verification.');
    } finally {
      setSavingId(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900">Student Verification Reviews</h1>
            <p className="mt-2 text-gray-500 font-medium">
              Review student discount requests without crowding the main admin dashboard.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {filters.map((status) => (
              <button
                key={status}
                type="button"
                onClick={() => setFilter(status)}
                className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
                  filter === status
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-600 border border-gray-200 hover:border-indigo-300 hover:text-indigo-600'
                }`}
              >
                {status}
              </button>
            ))}
          </div>
        </div>

        {error && <AlertMessage variant="error">{error}</AlertMessage>}
        {success && <AlertMessage variant="success">{success}</AlertMessage>}

        {verifications.length === 0 ? (
          <div className="bg-white rounded-3xl border border-gray-100 shadow-sm p-10 text-center">
            <BadgeCheck className="w-10 h-10 text-indigo-500 mx-auto mb-4" />
            <h2 className="text-lg font-bold text-gray-900">No {filter.toLowerCase()} requests</h2>
            <p className="mt-2 text-sm text-gray-500">
              Student verification requests will appear here when users submit them.
            </p>
          </div>
        ) : (
          <div className="space-y-6">
            {verifications.map((verification) => (
              <div key={verification.id} className="bg-white rounded-3xl border border-gray-100 shadow-sm overflow-hidden">
                <div className="p-6 border-b border-gray-100 flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-3">
                      <h2 className="text-xl font-bold text-gray-900">{verification.user_email}</h2>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold ${statusStyles[verification.status] || 'bg-gray-100 text-gray-700'}`}>
                        {verification.status}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-gray-500">
                      Submitted on {formatDateTime(verification.created_at)}
                    </p>
                  </div>

                  {verification.supporting_document && (
                    <a
                      href={verification.supporting_document}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 self-start rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-2 text-sm font-semibold text-indigo-700 hover:bg-indigo-100 transition-colors"
                    >
                      <FileText className="w-4 h-4" />
                      View Document
                    </a>
                  )}
                </div>

                <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-gray-400">Student Email</p>
                    <p className="mt-1 text-sm text-gray-700">{verification.student_email}</p>
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-gray-400">Student ID</p>
                    <p className="mt-1 text-sm text-gray-700">{verification.student_id}</p>
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-gray-400">Institution</p>
                    <p className="mt-1 text-sm text-gray-700">{verification.institution_name}</p>
                  </div>
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-gray-400">Reviewed By</p>
                    <p className="mt-1 text-sm text-gray-700">{verification.reviewed_by_email || 'Not reviewed yet'}</p>
                  </div>
                  <div className="md:col-span-2">
                    <p className="text-xs font-bold uppercase tracking-wider text-gray-400">Notes</p>
                    <p className="mt-1 text-sm text-gray-700 whitespace-pre-wrap">
                      {verification.notes || 'No additional notes provided.'}
                    </p>
                  </div>
                  {verification.rejection_reason && (
                    <div className="md:col-span-2">
                      <p className="text-xs font-bold uppercase tracking-wider text-gray-400">Rejection Reason</p>
                      <p className="mt-1 text-sm text-rose-700 whitespace-pre-wrap">{verification.rejection_reason}</p>
                    </div>
                  )}
                </div>

                {verification.status === 'PENDING' && (
                  <div className="px-6 pb-6">
                    <div className="rounded-2xl bg-gray-50 border border-gray-100 p-5 space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Rejection reason
                        </label>
                        <textarea
                          rows="3"
                          value={rejectionReasons[verification.id] || ''}
                          onChange={(event) =>
                            setRejectionReasons((current) => ({
                              ...current,
                              [verification.id]: event.target.value,
                            }))
                          }
                          placeholder="Only needed if you reject this request."
                          className="w-full rounded-xl border border-gray-200 px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                        />
                      </div>

                      <div className="flex flex-col gap-3 sm:flex-row">
                        <button
                          type="button"
                          disabled={savingId === verification.id}
                          onClick={() => handleReview(verification.id, 'APPROVED')}
                          className="inline-flex items-center justify-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 text-sm font-bold text-white hover:bg-emerald-700 transition-colors disabled:opacity-60"
                        >
                          {savingId === verification.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
                          Approve
                        </button>
                        <button
                          type="button"
                          disabled={savingId === verification.id}
                          onClick={() => handleReview(verification.id, 'REJECTED')}
                          className="inline-flex items-center justify-center gap-2 rounded-xl bg-rose-600 px-5 py-3 text-sm font-bold text-white hover:bg-rose-700 transition-colors disabled:opacity-60"
                        >
                          {savingId === verification.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <XCircle className="w-4 h-4" />}
                          Reject
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default AdminStudentVerifications;
