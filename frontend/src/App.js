import React, { useState } from 'react';
import EventList from './components/EventList';
import SeatMap from './components/SeatMap';
import BookingConfirmation from './components/BookingConfirmation';
import './styles/App.css';

const VIEWS = {
  EVENT_LIST: 'EVENT_LIST',
  SEAT_MAP: 'SEAT_MAP',
  CONFIRMATION: 'CONFIRMATION',
};

function App() {
  const [currentView, setCurrentView] = useState(VIEWS.EVENT_LIST);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [bookingData, setBookingData] = useState(null);

  const handleSelectEvent = (event) => {
    setSelectedEvent(event);
    setCurrentView(VIEWS.SEAT_MAP);
  };

  const handleBackToEvents = () => {
    setSelectedEvent(null);
    setBookingData(null);
    setCurrentView(VIEWS.EVENT_LIST);
  };

  const handleBookingComplete = (booking) => {
    setBookingData(booking);
    setCurrentView(VIEWS.CONFIRMATION);
  };

  return (
    <div className="app">
      <nav className="navbar">
        <div className="navbar-inner">
          <button
            className="nav-logo"
            onClick={handleBackToEvents}
          >
            <span className="logo-icon">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                <path d="M2 9.5V7a2 2 0 012-2h16a2 2 0 012 2v2.5" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/>
                <path d="M2 14.5V17a2 2 0 002 2h16a2 2 0 002-2v-2.5" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"/>
                <path d="M22 9.5a2 2 0 010 5M2 9.5a2 2 0 000 5" stroke="currentColor" strokeWidth="1.75"/>
              </svg>
            </span>
            <span className="logo-text">TicketFlow</span>
          </button>

          <div className="nav-breadcrumb">
            {currentView === VIEWS.SEAT_MAP && selectedEvent && (
              <>
                <button onClick={handleBackToEvents} className="breadcrumb-link">Events</button>
                <span className="breadcrumb-sep">›</span>
                <span className="breadcrumb-current">{selectedEvent.name}</span>
              </>
            )}
            {currentView === VIEWS.CONFIRMATION && (
              <>
                <button onClick={handleBackToEvents} className="breadcrumb-link">Events</button>
                <span className="breadcrumb-sep">›</span>
                <span className="breadcrumb-current">Confirmation</span>
              </>
            )}
          </div>

          <div className="nav-actions">
            <span className="nav-badge">
              <span className="badge-dot"></span>
              Live
            </span>
          </div>
        </div>
      </nav>

      <main className="app-content">
        {currentView === VIEWS.EVENT_LIST && (
          <EventList onSelectEvent={handleSelectEvent} />
        )}
        {currentView === VIEWS.SEAT_MAP && selectedEvent && (
          <SeatMap
            event={selectedEvent}
            onBack={handleBackToEvents}
            onBookingComplete={handleBookingComplete}
          />
        )}
        {currentView === VIEWS.CONFIRMATION && bookingData && (
          <BookingConfirmation
            bookingData={bookingData}
            onBackToEvents={handleBackToEvents}
          />
        )}
      </main>

      <footer className="app-footer">
        <div className="footer-inner">
          <span className="footer-logo">TicketFlow</span>
          <span className="footer-sep">·</span>
          <span className="footer-stack">AWS Lambda · DynamoDB · EventBridge · Redis</span>
        </div>
      </footer>
    </div>
  );
}

export default App;
