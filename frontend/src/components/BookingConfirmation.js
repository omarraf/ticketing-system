import React from 'react';
import '../styles/BookingConfirmation.css';

const BookingConfirmation = ({ bookingData, onBackToEvents }) => {
  const isPending = bookingData.payment_status === 'pending';
  const isConfirmed = bookingData.payment_status === 'confirmed';

  const steps = [
    { id: 1, label: 'Seat reserved', done: true },
    { id: 2, label: 'Payment processing', done: isConfirmed, active: isPending },
    { id: 3, label: 'Confirmation sent', done: isConfirmed, active: false },
  ];

  return (
    <div className="confirm-page">
      <div className="confirm-card">

        {/* Header */}
        <div className="confirm-header">
          <div className="confirm-icon-wrap">
            <div className="confirm-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
                <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div className="confirm-icon-ring"></div>
          </div>
          <h1>You're in!</h1>
          <p className="confirm-subtext">{bookingData.message || 'Your seat has been reserved.'}</p>
        </div>

        {/* Receipt */}
        <div className="receipt">
          <div className="receipt-header">
            <span className="receipt-label">Booking receipt</span>
            <span className="receipt-id">{bookingData.booking_id}</span>
          </div>

          <div className="receipt-rows">
            <div className="receipt-row">
              <span className="receipt-key">Event</span>
              <span className="receipt-val">{bookingData.event_name}</span>
            </div>
            <div className="receipt-row">
              <span className="receipt-key">Seat</span>
              <span className="receipt-val">
                {bookingData.seat_info
                  ? `Row ${bookingData.seat_info.row}, Seat ${bookingData.seat_info.number}`
                  : bookingData.seat_id}
              </span>
            </div>
            <div className="receipt-row">
              <span className="receipt-key">Section</span>
              <span className="receipt-val">{bookingData.seat_info?.section ?? '—'}</span>
            </div>
            <div className="receipt-row receipt-row--total">
              <span className="receipt-key">Total paid</span>
              <span className="receipt-val receipt-price">${bookingData.price}</span>
            </div>
          </div>
        </div>

        {/* Progress steps */}
        <div className="progress-steps">
          {steps.map((step, i) => (
            <React.Fragment key={step.id}>
              <div className={`step ${step.done ? 'step--done' : ''} ${step.active ? 'step--active' : ''}`}>
                <div className="step-dot">
                  {step.done && (
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none">
                      <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  )}
                  {step.active && <div className="step-pulse"></div>}
                </div>
                <span className="step-label">{step.label}</span>
              </div>
              {i < steps.length - 1 && <div className={`step-line ${step.done ? 'step-line--done' : ''}`}></div>}
            </React.Fragment>
          ))}
        </div>

        {/* Save booking ID notice */}
        <div className="save-notice">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          Save your booking ID <strong>{bookingData.booking_id}</strong> for support inquiries.
        </div>

        <div className="confirm-actions">
          <button onClick={onBackToEvents} className="btn-primary btn-full">
            Browse more events
          </button>
        </div>
      </div>
    </div>
  );
};

export default BookingConfirmation;
