import { useEffect, useState } from 'react';
import { FileBadge2, Loader2, ShieldCheck, Upload } from 'lucide-react';

import authService from '../services/authService';
import studentService from '../services/studentService';


const statusStyles = {
  APPROVED: 'bg-emerald-100 text-emerald-700',
  PENDING: 'bg-amber-100 text-amber-700',
  REJECTED: 'bg-red-100 text-red-700',
};

const formatDateTime = (value) => {
  if (!value) {
    return '';
  }

  return new Date(value).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};


function StudentVerification() {
  const user = authService.getCurrentUser();
  const token = user?.access || user?.token;

  const [formData, setFormData] = useState({
    student_email: '',
    student_id: '',
    institution_name: '',
    notes: '',
  });
  const [document, setDocument] = useState(null);
  const [verification, setVerification] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    const fetchVerification = async () => {
      try {
        const data = await studentService.getMyVerification(token);
        if (data) {
          setVerification(data);
          setFormData({
            student_email: data.student_email || '',
            student_id: data.student_id || '',
            institution_name: data.institution_name || '',
            notes: data.notes || '',
          });
        }
      } catch (fetchError) {
        setError(fetchError.message || 'Failed to load student verification.');
      } finally {
        setLoading(false);
      }
    };

    fetchVerification();
  }, [token]);

  const handleChange = (event) => {
    setFormData((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSaving(true);
    setError('');
    setSuccess('');

    const payload = new FormData();
    Object.entries(formData).forEach(([key, value]) => {
      payload.append(key, value);
    });
    if (document) {
      payload.append('student_id_image', document);
    }

    try {
      const data = await studentService.submitVerification(payload, token);
      setVerification(data);
      await authService.refreshProfile(token);
      setSuccess('Student verification submitted successfully.');
    } catch (submitError) {
      setError(submitError.message || 'Failed to submit student verification.');
    } finally {
      setSaving(false);
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
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-3xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-8 border-b border-gray-100 bg-gray-50/70">
            <div className="flex items-center gap-3 mb-4">
              <div className="bg-indigo-600 p-3 rounded-2xl text-white">
                <FileBadge2 className="w-6 h-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Student Verification</h1>
                <p className="text-sm text-gray-500">
                  Submit your student details to unlock discounted event pricing.
                </p>
              </div>
            </div>

            {verification && (
              <div>
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold bg-gray-100">
                  <ShieldCheck className="w-4 h-4" />
                  <span className={`px-2 py-1 rounded-full ${statusStyles[verification.status] || 'bg-gray-100 text-gray-700'}`}>
                    {verification.status}
                  </span>
                </div>
                {verification.verified_at && (
                  <p className="mt-3 text-sm text-emerald-700 font-medium">
                    Verified on {formatDateTime(verification.verified_at)}
                  </p>
                )}
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="p-8 space-y-6">
            {error && <div className="bg-red-50 border border-red-100 text-red-600 p-4 rounded-2xl">{error}</div>}
            {success && <div className="bg-emerald-50 border border-emerald-100 text-emerald-700 p-4 rounded-2xl">{success}</div>}

            {verification?.rejection_reason && (
              <div className="bg-amber-50 border border-amber-100 text-amber-700 p-4 rounded-2xl">
                Rejection reason: {verification.rejection_reason}
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Student Email</label>
                <input
                  type="email"
                  name="student_email"
                  required
                  value={formData.student_email}
                  onChange={handleChange}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div className="space-y-2">
                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Student ID</label>
                <input
                  type="text"
                  name="student_id"
                  required
                  value={formData.student_id}
                  onChange={handleChange}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div className="space-y-2 md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Institution</label>
                <input
                  type="text"
                  name="institution_name"
                  required
                  value={formData.institution_name}
                  onChange={handleChange}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none"
                />
              </div>

              <div className="space-y-2 md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Supporting Document</label>
                <label className="flex items-center justify-center gap-2 border border-dashed border-gray-300 rounded-2xl px-4 py-6 text-gray-500 hover:border-indigo-400 hover:text-indigo-600 transition-colors cursor-pointer">
                  <Upload className="w-5 h-5" />
                  <span>{document?.name || 'Upload student ID or proof document'}</span>
                  <input
                    type="file"
                    className="hidden"
                    onChange={(event) => setDocument(event.target.files?.[0] || null)}
                  />
                </label>
              </div>

              <div className="space-y-2 md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Notes</label>
                <textarea
                  name="notes"
                  rows="4"
                  value={formData.notes}
                  onChange={handleChange}
                  className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 outline-none resize-none"
                  placeholder="Add any extra context for the admin review."
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={saving}
              className="w-full bg-indigo-600 text-white font-bold py-4 rounded-2xl hover:bg-indigo-700 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {saving ? <Loader2 className="w-5 h-5 animate-spin" /> : <ShieldCheck className="w-5 h-5" />}
              {verification ? 'Update Verification Request' : 'Submit Verification'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}


export default StudentVerification;
