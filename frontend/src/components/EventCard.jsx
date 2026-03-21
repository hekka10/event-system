import { Link } from 'react-router-dom';
import { Calendar, MapPin, Tag } from 'lucide-react';

const EventCard = ({ event }) => {
    const formattedDate = new Date(event.date).toLocaleDateString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        year: 'numeric',
    });

    return (
        <div className="bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow overflow-hidden border border-gray-100 flex flex-col h-full">
            <div className="relative h-48 overflow-hidden">
                {event.image ? (
                    <img
                        src={event.image}
                        alt={event.title}
                        className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
                    />
                ) : (
                    <div className="w-full h-full bg-indigo-50 flex items-center justify-center">
                        <Tag className="w-12 h-12 text-indigo-200" />
                    </div>
                )}
                <div className="absolute top-4 left-4 flex gap-2">
                    <span className="bg-white/90 backdrop-blur-sm text-indigo-600 text-xs font-semibold px-2.5 py-1 rounded-full shadow-sm">
                        {event.category_name || 'Event'}
                    </span>
                    {!event.is_approved && (
                        <span className="bg-amber-100/90 backdrop-blur-sm text-amber-600 text-xs font-semibold px-2.5 py-1 rounded-full shadow-sm border border-amber-200">
                            Pending Approval
                        </span>
                    )}
                </div>
            </div>

            <div className="p-5 flex flex-col flex-grow">
                <h3 className="text-xl font-bold text-gray-900 mb-2 line-clamp-1">{event.title}</h3>

                <div className="space-y-2 mb-4">
                    <div className="flex items-center text-sm text-gray-500">
                        <Calendar className="w-4 h-4 mr-2 text-indigo-500" />
                        <span>{formattedDate}</span>
                    </div>
                    <div className="flex items-center text-sm text-gray-500">
                        <MapPin className="w-4 h-4 mr-2 text-indigo-500" />
                        <span className="line-clamp-1">{event.location}</span>
                    </div>
                </div>

                <p className="text-gray-600 text-sm line-clamp-2 mb-4 flex-grow">
                    {event.description}
                </p>

                <div className="flex items-center justify-between pt-4 border-t border-gray-50 mt-auto">
                    <span className="text-lg font-bold text-indigo-600">
                        {event.price > 0 ? `$${event.price}` : 'Free'}
                    </span>
                    <Link
                        to={`/events/${event.id}`}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
                    >
                        View Details
                    </Link>
                </div>
            </div>
        </div>
    );
};

export default EventCard;
