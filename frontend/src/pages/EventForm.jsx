import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import eventService from '../services/eventService';
import authService from '../services/authService';
import { Camera, Save, X, Loader2, AlertCircle } from 'lucide-react';

function EventForm() {
    const { id } = useParams();
    const isEditMode = !!id;
    const navigate = useNavigate();
    const user = authService.getCurrentUser();

    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(false);
    const [initialLoading, setInitialLoading] = useState(isEditMode);
    const [error, setError] = useState(null);

    const [formData, setFormData] = useState({
        title: '',
        description: '',
        date: '',
        location: '',
        category: '',
        price: '0.00',
        capacity: '100',
    });
    const [imageFile, setImageFile] = useState(null);
    const [imagePreview, setImagePreview] = useState(null);

    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }
        fetchCategories();
        if (isEditMode) {
            fetchEventDetails();
        }
    }, [id]);

    const fetchCategories = async () => {
        try {
            const data = await eventService.getCategories();
            setCategories(data);
        } catch (err) {
            console.error('Error fetching categories:', err);
        }
    };

    const fetchEventDetails = async () => {
        try {
            const data = await eventService.getEventById(id);
            // Format date for input type="datetime-local"
            const date = new Date(data.date);
            const formattedDate = date.toISOString().slice(0, 16);

            setFormData({
                title: data.title,
                description: data.description,
                date: formattedDate,
                location: data.location,
                category: data.category || '',
                price: data.price,
                capacity: data.capacity,
            });
            if (data.image) {
                setImagePreview(data.image);
            }
        } catch (err) {
            setError('Failed to fetch event details.');
        } finally {
            setInitialLoading(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleImageChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setImageFile(file);
            const reader = new FileReader();
            reader.onloadend = () => {
                setImagePreview(reader.result);
            };
            reader.readAsDataURL(file);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        const data = new FormData();
        Object.keys(formData).forEach(key => {
            data.append(key, formData[key]);
        });
        if (imageFile) {
            data.append('image', imageFile);
        }

        try {
            if (isEditMode) {
                await eventService.updateEvent(id, data, user.access || user.token);
            } else {
                await eventService.createEvent(data, user.access || user.token);
            }
            navigate('/events');
        } catch (err) {
            setError(err.message || 'Something went wrong.');
        } finally {
            setLoading(false);
        }
    };

    if (initialLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <Loader2 className="w-10 h-10 text-indigo-600 animate-spin" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-3xl mx-auto">
                <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="p-8 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                        <div>
                            <h1 className="text-2xl font-bold text-gray-900">{isEditMode ? 'Edit Event' : 'Create New Event'}</h1>
                            <p className="text-sm text-gray-500 mt-1">Fill in the details to {isEditMode ? 'update your' : 'host a new'} event.</p>
                        </div>
                        <button
                            onClick={() => navigate(-1)}
                            className="p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100 transition-colors"
                        >
                            <X className="w-6 h-6" />
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="p-8 space-y-6">
                        {error && (
                            <div className="bg-red-50 border border-red-100 text-red-600 p-4 rounded-xl flex items-center gap-3 text-sm">
                                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                                <p>{error}</p>
                            </div>
                        )}

                        {/* Image Upload */}
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Event Banner</label>
                            <div
                                className={`relative h-64 w-full rounded-2xl border-2 border-dashed transition-all flex flex-col items-center justify-center overflow-hidden
                  ${imagePreview ? 'border-transparent' : 'border-gray-300 hover:border-indigo-400 bg-gray-50'}`}
                            >
                                {imagePreview ? (
                                    <>
                                        <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />
                                        <button
                                            type="button"
                                            onClick={() => { setImageFile(null); setImagePreview(null); }}
                                            className="absolute top-4 right-4 p-2 bg-white/90 backdrop-blur-sm rounded-full shadow-sm text-red-500 hover:bg-red-50 transition-colors"
                                        >
                                            <X className="w-4 h-4" />
                                        </button>
                                    </>
                                ) : (
                                    <div className="text-center">
                                        <Camera className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                                        <p className="text-sm text-gray-500">Click to upload image</p>
                                        <p className="text-xs text-gray-400 mt-1">PNG, JPG up to 10MB</p>
                                    </div>
                                )}
                                <input
                                    type="file"
                                    onChange={handleImageChange}
                                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                    accept="image/*"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Event Title</label>
                                <input
                                    type="text"
                                    name="title"
                                    required
                                    value={formData.title}
                                    onChange={handleChange}
                                    placeholder="e.g. Annual Tech Conference 2024"
                                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none"
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Category</label>
                                <select
                                    name="category"
                                    required
                                    value={formData.category}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none bg-white"
                                >
                                    <option value="">Select a category</option>
                                    {categories.map(cat => (
                                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Date & Time</label>
                                <input
                                    type="datetime-local"
                                    name="date"
                                    required
                                    value={formData.date}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none"
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Location</label>
                                <input
                                    type="text"
                                    name="location"
                                    required
                                    value={formData.location}
                                    onChange={handleChange}
                                    placeholder="e.g. Grand Hall, City Center"
                                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none"
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Price ($)</label>
                                <input
                                    type="number"
                                    name="price"
                                    required
                                    min="0"
                                    step="0.01"
                                    value={formData.price}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none"
                                />
                            </div>

                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Capacity</label>
                                <input
                                    type="number"
                                    name="capacity"
                                    required
                                    min="1"
                                    value={formData.capacity}
                                    onChange={handleChange}
                                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none"
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Description</label>
                            <textarea
                                name="description"
                                required
                                rows="4"
                                value={formData.description}
                                onChange={handleChange}
                                placeholder="Describe your event in detail..."
                                className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none resize-none"
                            ></textarea>
                        </div>

                        <div className="pt-6 border-t border-gray-100 flex gap-4">
                            <button
                                type="button"
                                onClick={() => navigate(-1)}
                                className="flex-1 px-6 py-4 rounded-xl border border-gray-200 font-semibold text-gray-600 hover:bg-gray-50 transition-colors"
                                disabled={loading}
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                className="flex-3 bg-indigo-600 text-white px-8 py-4 rounded-xl font-bold hover:bg-indigo-700 transition-all shadow-lg shadow-indigo-100 active:scale-[0.98] flex items-center justify-center gap-2 min-w-[200px]"
                                disabled={loading}
                            >
                                {loading ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    <Save className="w-5 h-5" />
                                )}
                                {isEditMode ? 'Update Event' : 'Create Event'}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    );
}

export default EventForm;
