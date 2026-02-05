import React from 'react';
import { Calendar, Users, CreditCard, Bell, Search, ChevronDown } from 'lucide-react';

export default function EventFlowHomepage() {
  const events = [
    {
      title: "Tech Conference 2024",
      date: "October 15, 2024",
      location: "San Francisco, CA",
      price: "Free",
      category: "Conference",
      image: "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=400&h=250&fit=crop"
    },
    {
      title: "Annual Student Art Exhibition",
      date: "November 20, 2024",
      location: "New York University",
      price: "$25.00",
      category: "Exhibition",
      image: "https://images.unsplash.com/photo-1460661419201-fd4cecdf8a8b?w=400&h=250&fit=crop"
    },
    {
      title: "Music Festival Live",
      date: "September 18, 2024",
      location: "Central Park",
      price: "$45.00",
      category: "Music",
      image: "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=400&h=250&fit=crop"
    },
    {
      title: "Career Opportunities Fair",
      date: "October 10, 2024",
      location: "Boston Convention Center",
      price: "Free",
      category: "Career Fair",
      image: "https://images.unsplash.com/photo-1511578314322-379afb476865?w=400&h=250&fit=crop"
    },
    {
      title: "Annual Sports Day",
      date: "November 5, 2024",
      location: "Stanford Stadium",
      price: "Free",
      category: "Sports",
      image: "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?w=400&h=250&fit=crop"
    },
    {
      title: "Alumni Networking Mixer",
      date: "December 12, 2024",
      location: "Chicago Hilton",
      price: "$30.00",
      category: "Networking",
      image: "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=400&h=250&fit=crop"
    },
    {
      title: "Debate Club Showcase",
      date: "October 25, 2024",
      location: "Harvard Law School",
      price: "Free",
      category: "Academic",
      image: "https://images.unsplash.com/photo-1475721027785-f74eccf877e2?w=400&h=250&fit=crop"
    },
    {
      title: "Advanced Coding Workshop",
      date: "November 8, 2024",
      location: "MIT Campus",
      price: "$50.00",
      category: "Workshop",
      image: "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=400&h=250&fit=crop"
    },
    {
      title: "Literary Reading Series",
      date: "December 3, 2024",
      location: "Columbia University",
      price: "Free",
      category: "Arts & Culture",
      image: "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=400&h=250&fit=crop"
    }
  ];

  const features = [
    {
      icon: <Calendar className="w-8 h-8" />,
      title: "Browse Events",
      description: "Explore a wide variety of campus events tailored to your interests."
    },
    {
      icon: <Users className="w-8 h-8" />,
      title: "Verify Student ID",
      description: "Quick and easy student verification for exclusive campus events."
    },
    {
      icon: <CreditCard className="w-8 h-8" />,
      title: "Pay Securely",
      description: "Safe and secure payment processing for event tickets."
    },
    {
      icon: <Bell className="w-8 h-8" />,
      title: "Receive QR Ticket",
      description: "Get your QR code ticket instantly delivered to your email."
    }
  ];

  const benefits = [
    {
      title: "Student Verification & Integration",
      description: "Easily authenticate student status and integrate with school systems for seamless event access."
    },
    {
      title: "Secure Online Payments",
      description: "Pay for events with confidence using our encrypted payment gateway."
    },
    {
      title: "Flexible & Secure Check-In",
      description: "Use QR codes for fast, contactless check-in at any campus event."
    },
    {
      title: "QR Ticket & Email Confirmation",
      description: "Receive instant QR tickets via email for easy access to all your events."
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}


      {/* Hero Section */}
      <section className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <div>
              <h1 className="text-5xl font-bold text-gray-900 mb-6">
                Discover and Book Campus Events Easily
              </h1>
              <p className="text-lg text-gray-600 mb-8">
                Explore campus events, exclusive workshops, and activities designed for students. Book and get instant tickets for all university events.
              </p>
              <div className="flex gap-4">
                <button className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 font-medium">
                  Get Started
                </button>
                <button className="border border-gray-300 text-gray-700 px-8 py-3 rounded-lg hover:bg-gray-50 font-medium">
                  Learn More
                </button>
              </div>
            </div>
            <div className="relative">
              <img
                src="https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=600&h=400&fit=crop"
                alt="Campus Events"
                className="rounded-2xl shadow-2xl"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Search Bar */}
      <section className="bg-white py-8 border-t border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-4 items-center">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search events..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-600 focus:border-transparent"
              />
            </div>
            <div className="flex gap-4">
              <select className="px-4 py-2 border border-gray-300 rounded-lg">
                <option>Date</option>
              </select>
              <select className="px-4 py-2 border border-gray-300 rounded-lg">
                <option>Entry</option>
              </select>
              <select className="px-4 py-2 border border-gray-300 rounded-lg">
                <option>Keyword</option>
              </select>
              <select className="px-4 py-2 border border-gray-300 rounded-lg">
                <option>Date When</option>
              </select>
            </div>
          </div>
        </div>
      </section>

      {/* Events Grid */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-10 text-center">
            Upcoming Campus Events
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {events.map((event, index) => (
              <div key={index} className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-shadow">
                <img
                  src={event.image}
                  alt={event.title}
                  className="w-full h-48 object-cover"
                />
                <div className="p-6">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">{event.title}</h3>
                  <div className="space-y-2 mb-4">
                    <p className="text-sm text-gray-600 flex items-center">
                      <Calendar className="w-4 h-4 mr-2" />
                      {event.date}
                    </p>
                    <p className="text-sm text-gray-600">{event.location}</p>
                  </div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-lg font-bold text-gray-900">{event.price}</span>
                    <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                      {event.category}
                    </span>
                  </div>
                  <button className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 font-medium">
                    Register
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Use Platform */}
      <section className="bg-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-12 text-center">
            Why Use This Platform?
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {benefits.map((benefit, index) => (
              <div key={index} className="text-center">
                <h3 className="text-lg font-bold text-gray-900 mb-3">{benefit.title}</h3>
                <p className="text-gray-600 text-sm">{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-12 text-center">
            How It Works
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 text-blue-600 rounded-full mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-bold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600 text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}

    </div>
  );
}