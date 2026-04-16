import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import AlertMessage from '../components/AlertMessage';
import authService from '../services/authService';
import { Mail, Lock, Loader2, ArrowRight, ShieldCheck } from 'lucide-react';
import GoogleSignInButton from '../components/GoogleSignInButton';

const hasGoogleAuth = Boolean(import.meta.env.VITE_GOOGLE_CLIENT_ID);

function Login() {
    const [formData, setFormData] = useState({
        email: '',
        password: '',
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const location = useLocation();
    const redirectTo = location.state?.from?.pathname || '/';
    const notice = location.state?.message || '';

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await authService.login(formData);
            navigate(redirectTo, { replace: true });
        } catch (err) {
            setError(err.message || 'Login failed. Please check your credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-[calc(100-64px)] flex items-center justify-center bg-gray-50/50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full">
                <div className="bg-white p-10 rounded-[2.5rem] shadow-xl shadow-indigo-100/50 border border-gray-100">
                    <div className="text-center mb-10">
                        <div className="bg-indigo-600 w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-indigo-200">
                            <ShieldCheck className="w-8 h-8 text-white" />
                        </div>
                        <h2 className="text-3xl font-extrabold text-gray-900">Welcome Back</h2>
                        <p className="mt-2 text-gray-500 font-medium">Log in to manage your events</p>
                    </div>

                    <form className="space-y-6" onSubmit={handleSubmit}>
                        {notice && (
                            <AlertMessage variant="success" centered>
                                {notice}
                            </AlertMessage>
                        )}

                        {error && (
                            <AlertMessage variant="error" centered className="italic">
                                {error}
                            </AlertMessage>
                        )}

                        <div className="space-y-4">
                            <div className="relative group">
                                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-indigo-600 transition-colors" />
                                <input
                                    name="email"
                                    type="email"
                                    required
                                    className="w-full pl-12 pr-4 py-4 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-indigo-600 outline-none text-gray-900 transition-all font-medium"
                                    placeholder="Email address"
                                    value={formData.email}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="relative group">
                                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 group-focus-within:text-indigo-600 transition-colors" />
                                <input
                                    name="password"
                                    type="password"
                                    required
                                    className="w-full pl-12 pr-4 py-4 bg-gray-50 border border-gray-100 rounded-2xl focus:ring-2 focus:ring-indigo-600 outline-none text-gray-900 transition-all font-medium"
                                    placeholder="Password"
                                    value={formData.password}
                                    onChange={handleChange}
                                />
                            </div>
                            <div className="flex justify-end">
                                <Link
                                    to="/forgot-password"
                                    className="text-sm font-semibold text-indigo-600 hover:text-indigo-700 underline underline-offset-4"
                                >
                                    Forgot password?
                                </Link>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full flex justify-center items-center gap-2 py-4 px-4 bg-indigo-600 text-white font-bold rounded-2xl hover:bg-indigo-700 focus:outline-none focus:ring-4 focus:ring-indigo-100 transition-all shadow-lg shadow-indigo-100 active:scale-[0.98] disabled:opacity-50"
                        >
                            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Log in'}
                            {!loading && <ArrowRight className="w-5 h-5" />}
                        </button>
                    </form>

                    <div className="mt-10 text-center">
                        {hasGoogleAuth && (
                            <>
                                <div className="mb-6">
                                    <GoogleSignInButton
                                        onSuccess={() => navigate(redirectTo, { replace: true })}
                                        onError={(googleError) =>
                                            setError(googleError.message || 'Google login is not available right now.')
                                        }
                                    />
                                </div>

                                <div className="relative mb-6">
                                    <div className="absolute inset-0 flex items-center">
                                        <div className="w-full border-t border-gray-100" />
                                    </div>
                                    <div className="relative flex justify-center text-xs uppercase tracking-[0.2em] text-gray-400">
                                        <span className="bg-white px-3">or continue with email</span>
                                    </div>
                                </div>
                            </>
                        )}

                        <p className="text-gray-500 font-medium">
                            Don't have an account?{' '}
                            <Link to="/signup" className="text-indigo-600 font-bold hover:text-indigo-700 underline underline-offset-4">
                                Sign up
                            </Link>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Login;
