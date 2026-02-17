import React, { useState, useEffect } from 'react';
import { getEvents } from '../services/api';
import '../styles/EventList.css';

const EventList = ({ onSelectEvent }) => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { fetchEvents(); }, []);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getEvents();
      setEvents(data);
    } catch (err) {
      setError('Failed to load events. Check your API connection.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return {
      day: date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
      time: date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      year: date.getFullYear(),
    };
  };

  const getAvailabilityPct = (event) =>
    Math.round((event.available_seats / event.total_seats) * 100);

  const getEventAccent = (index) => {
    const accents = ['#7c6af7', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
    return accents[index % accents.length];
  };

  if (loading) {
    return (
      <div className="page-container">
        <div className="skeleton-header">
          <div className="skeleton-line skeleton-title"></div>
          <div className="skeleton-line skeleton-sub"></div>
        </div>
        <div className="events-grid">
          {[1, 2, 3].map(i => (
            <div key={i} className="event-card skeleton-card">
              <div className="skeleton-card-header"></div>
              <div className="skeleton-body">
                <div className="skeleton-line"></div>
                <div className="skeleton-line skeleton-short"></div>
                <div className="skeleton-line skeleton-short"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page-container">
        <div className="error-state">
          <div className="error-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5"/>
              <path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <h3>Unable to load events</h3>
          <p>{error}</p>
          <button onClick={fetchEvents} className="btn-primary">Try again</button>
        </div>
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className="page-container">
        <div className="empty-state">
          <div className="empty-icon">🎭</div>
          <h3>No events available</h3>
          <p>Check back soon for upcoming events.</p>
          <button onClick={fetchEvents} className="btn-ghost">Refresh</button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">Upcoming Events</h1>
          <p className="page-subtitle">{events.length} event{events.length !== 1 ? 's' : ''} available · Select one to choose your seats</p>
        </div>
        <button onClick={fetchEvents} className="btn-ghost btn-sm">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Refresh
        </button>
      </div>

      <div className="events-grid">
        {events.map((event, index) => {
          const date = formatDate(event.date);
          const pct = getAvailabilityPct(event);
          const accent = getEventAccent(index);
          const soldOut = event.available_seats === 0;
          const limited = !soldOut && pct < 20;

          return (
            <div
              key={event.event_id}
              className={`event-card ${soldOut ? 'event-card--sold-out' : ''}`}
              onClick={() => !soldOut && onSelectEvent(event)}
              style={{ '--accent': accent }}
            >
              <div className="event-card-accent"></div>

              <div className="event-card-body">
                <div className="event-card-top">
                  <div className="event-meta-row">
                    <span className="event-date-badge">
                      {date.day} · {date.time}
                    </span>
                    {soldOut && <span className="tag tag--red">Sold out</span>}
                    {limited && <span className="tag tag--amber">Few left</span>}
                  </div>
                  <h3 className="event-name">{event.name}</h3>
                  <p className="event-venue">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                      <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" stroke="currentColor" strokeWidth="2"/>
                      <circle cx="12" cy="9" r="2.5" stroke="currentColor" strokeWidth="2"/>
                    </svg>
                    {event.venue}
                  </p>
                  {event.description && (
                    <p className="event-desc">{event.description}</p>
                  )}
                </div>

                <div className="event-card-bottom">
                  <div className="seat-availability">
                    <div className="seat-bar-header">
                      <span className="seat-bar-label">Availability</span>
                      <span className="seat-bar-count">
                        {event.available_seats} <span>/ {event.total_seats}</span>
                      </span>
                    </div>
                    <div className="seat-bar-track">
                      <div
                        className="seat-bar-fill"
                        style={{ width: `${pct}%`, background: soldOut ? '#374151' : accent }}
                      ></div>
                    </div>
                  </div>

                  <div className="event-card-footer">
                    <div className="event-price">
                      <span className="price-amount">${event.price}</span>
                      <span className="price-label">/ ticket</span>
                    </div>
                    <button
                      className={`btn-cta ${soldOut ? 'btn-cta--disabled' : ''}`}
                      disabled={soldOut}
                      tabIndex={-1}
                    >
                      {soldOut ? 'Sold out' : 'Choose seats'}
                      {!soldOut && (
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                          <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default EventList;
