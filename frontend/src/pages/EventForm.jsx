import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import eventService from '../services/eventService';
import authService from '../services/authService';
import { Camera, Save, X, Loader2, AlertCircle } from 'lucide-react';
import LocationPicker from '../components/LocationPicker';

const getLocalDateTimeValue = (value) => {
    if (!value) {
        return '';
    }

    const date = new Date(value);
    const timezoneOffset = date.getTimezoneOffset() * 60000;
    return new Date(date.getTime() - timezoneOffset).toISOString().slice(0, 16);
};

const validateFormData = (formData) => {
    const nextErrors = {};

    if (!formData.title.trim()) {
        nextErrors.title = 'Title is required.';
    }

    if (!formData.location.trim()) {
        nextErrors.location = 'Location is required.';
    }

    if (!formData.category) {
        nextErrors.category = 'Please select a category.';
    }

    if (!formData.date) {
        nextErrors.date = 'Date and time are required.';
    } else {
        const parsed = new Date(formData.date);
        if (isNaN(parsed.getTime()) || parsed.getFullYear() > 2100) {
            nextErrors.date = 'Please enter a valid date (year <= 2100).';
        } else if (parsed <= new Date()) {
            nextErrors.date = 'Please choose a future date and time.';
        }
    }

    if (Number(formData.capacity) <= 0) {
        nextErrors.capacity = 'Capacity must be greater than 0.';
    }

    if (Number(formData.price) < 0) {
        nextErrors.price = 'Price cannot be negative.';
    }

    if (formData.google_maps_link) {
        try {
            new URL(formData.google_maps_link);
        } catch {
            nextErrors.google_maps_link = 'Enter a valid Google Maps link.';
        }
    }

    if (
        formData.latitude !== '' &&
        (Number.isNaN(Number(formData.latitude)) || Number(formData.latitude) < -90 || Number(formData.latitude) > 90)
    ) {
        nextErrors.latitude = 'Latitude must be between -90 and 90.';
    }

    if (
        formData.longitude !== '' &&
        (Number.isNaN(Number(formData.longitude)) || Number(formData.longitude) < -180 || Number(formData.longitude) > 180)
    ) {
        nextErrors.longitude = 'Longitude must be between -180 and 180.';
    }

    return nextErrors;
};

function EventForm() {
    const { id } = useParams();
    const isEditMode = !!id;
    const navigate = useNavigate();
    const user = authService.getCurrentUser();
    const token = user?.access || user?.token || '';

    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(false);
    const [initialLoading, setInitialLoading] = useState(isEditMode);
    const [error, setError] = useState(null);
    const [fieldErrors, setFieldErrors] = useState({});

    const [formData, setFormData] = useState({
        title: '',
        description: '',
        date: '',
        location: '',
        parking_info: '',
        google_maps_link: '',
        latitude: '',
        longitude: '',
        category: '',
        price: '0.00',
        capacity: '100',
    });
    const [imageFile, setImageFile] = useState(null);
    const [imagePreview, setImagePreview] = useState(null);

    useEffect(() => {
        if (!token) {
            navigate('/login');
            return;
        }
        const loadFormData = async () => {
            try {
                const categoriesData = await eventService.getCategories();
                setCategories(categoriesData);
            } catch (categoryError) {
                console.error('Error fetching categories:', categoryError);
            }

            if (!isEditMode) {
                return;
            }

            try {
                const data = await eventService.getEventById(id, token);
                setFormData({
                    title: data.title,
                    description: data.description,
                    date: getLocalDateTimeValue(data.date),
                    location: data.location,
                    parking_info: data.parking_info || '',
                    google_maps_link: data.google_maps_link || data.parking_map_url || '',
                    latitude: data.latitude || '',
                    longitude: data.longitude || '',
                    category: data.category || '',
                    price: data.price,
                    capacity: data.capacity,
                });
                if (data.image) {
                    setImagePreview(data.image);
                }
            } catch {
                setError('Failed to fetch event details.');
            } finally {
                setInitialLoading(false);
            }
        };

        loadFormData();
    }, [id, isEditMode, navigate, token]);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFieldErrors(prev => ({ ...prev, [name]: undefined }));
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleLocationSelect = async (lat, lng) => {
        setFormData(prev => ({ ...prev, latitude: lat, longitude: lng }));
        try {
            const res = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lng}&format=json`);
            const data = await res.json();
            if (data && data.display_name) {
                setFormData(prev => ({ ...prev, location: data.display_name }));
                setFieldErrors(prev => ({ ...prev, location: undefined, latitude: undefined, longitude: undefined }));
            }
        } catch (err) {
            console.error('Failed to reverse geocode', err);
        }
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
        const nextErrors = validateFormData(formData);
        if (Object.keys(nextErrors).length > 0) {
            setFieldErrors(nextErrors);
            setError('Please fix the highlighted fields.');
            return;
        }

        setLoading(true);
        setError(null);
        setFieldErrors({});

        const data = new FormData();
        Object.keys(formData).forEach(key => {
            if (formData[key] !== '') {
                if (key === 'date') {
                    try {
                        const dateObj = new Date(formData.date);
                        data.append(key, dateObj.toISOString());
                    } catch {
                        data.append(key, formData[key]);
                    }
                } else {
                    data.append(key, formData[key]);
                }
            }
        });
        if (imageFile) {
            data.append('image', imageFile);
        }

        try {
            if (isEditMode) {
                const updatedEvent = await eventService.updateEvent(id, data, token);
                navigate(`/events/${updatedEvent.id}`, {
                    replace: true,
                    state: { message: 'Event updated successfully.' },
                });
            } else {
                const createdEvent = await eventService.createEvent(data, token);
                navigate(`/events/${createdEvent.id}`, {
                    replace: true,
                    state: { message: 'Event created successfully. It is pending admin approval.' },
                });
            }
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
                                {fieldErrors.title && <p className="text-sm text-red-600">{fieldErrors.title}</p>}
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
                                {fieldErrors.category && <p className="text-sm text-red-600">{fieldErrors.category}</p>}
                                {categories.length === 0 && (
                                    <p className="text-sm text-amber-600">
                                        No categories are available yet. Ask an admin to create one before publishing an event.
                                    </p>
                                )}
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
                                {fieldErrors.date && <p className="text-sm text-red-600">{fieldErrors.date}</p>}
                            </div>

                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Location Name/Address</label>
                                <input
                                    type="text"
                                    name="location"
                                    required
                                    value={formData.location}
                                    onChange={handleChange}
                                    placeholder="Type or click map to auto-fill"
                                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none"
                                />
                                {fieldErrors.location && <p className="text-sm text-red-600">{fieldErrors.location}</p>}
                            </div>

                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Price (NRs)</label>
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
                                {fieldErrors.price && <p className="text-sm text-red-600">{fieldErrors.price}</p>}
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
                                {fieldErrors.capacity && <p className="text-sm text-red-600">{fieldErrors.capacity}</p>}
                            </div>

                            <div className="space-y-2 md:col-span-2">
                                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Parking Info</label>
                                <textarea
                                    name="parking_info"
                                    rows="3"
                                    value={formData.parking_info}
                                    onChange={handleChange}
                                    placeholder="Share parking guidance, entry gates, landmarks, or restrictions."
                                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none resize-none"
                                />
                            </div>

                            <div className="space-y-2 md:col-span-2">
                                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Google Maps Link</label>
                                <input
                                    type="url"
                                    name="google_maps_link"
                                    value={formData.google_maps_link}
                                    onChange={handleChange}
                                    placeholder="https://maps.google.com/..."
                                    className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all outline-none"
                                />
                                {fieldErrors.google_maps_link && <p className="text-sm text-red-600">{fieldErrors.google_maps_link}</p>}
                            </div>

                            <div className="space-y-2 md:col-span-2">
                                <label className="block text-sm font-medium text-gray-700 uppercase tracking-wider">Map Location</label>
                                <LocationPicker 
                                    latitude={formData.latitude} 
                                    longitude={formData.longitude} 
                                    onLocationSelect={handleLocationSelect} 
                                />
                                {(fieldErrors.latitude || fieldErrors.longitude) && 
                                    <p className="text-sm text-red-600">Please select a location on the map.</p>
                                }
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
