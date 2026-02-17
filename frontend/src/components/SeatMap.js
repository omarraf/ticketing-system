import React, { useState, useEffect } from 'react';
import { getSeats, reserveSeat } from '../services/api';
import '../styles/SeatMap.css';

const SeatMap = ({ event, onBack, onBookingComplete }) => {
  const [seatMap, setSeatMap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedSeat, setSelectedSeat] = useState(null);
  const [reserving, setReserving] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [lastUpdated, setLastUpdated] = useState(null);

  useEffect(() => {
    fetchSeats();
    const interval = setInterval(fetchSeats, 5000);
    return () => clearInterval(interval);
  }, [event.event_id]);

  const fetchSeats = async () => {
    try {
      setError(null);
      const data = await getSeats(event.event_id);
      setSeatMap(data);
      setLastUpdated(new Date());
    } catch (err) {
      setError('Failed to load seat map.');
    } finally {
      setLoading(false);
    }
  };

  const handleSeatClick = (seat) => {
    if (seat.status === 'available') {
      setSelectedSeat(prev => prev?.seat_id === seat.seat_id ? null : seat);
    }
  };

  const handleReservation = async () => {
    if (!selectedSeat) return;
    try {
      setReserving(true);
      setError(null);
      const userId = `user-${Date.now()}`;
      const response = await reserveSeat({
        event_id: event.event_id,
        seat_id: selectedSeat.seat_id,
        user_id: userId,
        email: userEmail || undefined,
      });
      onBookingComplete({ ...response, event_name: event.name, seat_info: selectedSeat });
    } catch (err) {
      setError(err.message || 'Reservation failed. Please try again.');
      fetchSeats();
      setSelectedSeat(null);
    } finally {
      setReserving(false);
    }
  };

  const organizeSeatsByRow = () => {
    if (!seatMap?.seats) return {};
    const rows = {};
    seatMap.seats.forEach(seat => {
      if (!rows[seat.row]) rows[seat.row] = [];
      rows[seat.row].push(seat);
    });
    Object.keys(rows).forEach(row => rows[row].sort((a, b) => a.number - b.number));
    return rows;
  };

  const getSeatClass = (seat) => {
    const base = 'seat';
    if (seat.status === 'available') {
      return selectedSeat?.seat_id === seat.seat_id ? `${base} seat--selected` : `${base} seat--available`;
    }
    if (seat.status === 'reserved') return `${base} seat--reserved`;
    if (seat.status === 'sold') return `${base} seat--sold`;
    return base;
  };

  const sold = seatMap ? seatMap.total_seats - seatMap.available_seats : 0;
  const pct = seatMap ? Math.round((sold / seatMap.total_seats) * 100) : 0;

  if (loading) {
    return (
      <div className="seatmap-page">
        <div className="loading-center">
          <div className="spinner"></div>
          <p>Loading seat map…</p>
        </div>
      </div>
    );
  }

  const seatRows = organizeSeatsByRow();
  const sortedRowKeys = Object.keys(seatRows).sort();

  return (
    <div className="seatmap-page">
      <div className="seatmap-layout">

        {/* Left: Seat grid */}
        <div className="seatmap-main">
          <div className="seatmap-event-header">
            <button onClick={onBack} className="back-btn">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M19 12H5M12 5l-7 7 7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              Back
            </button>
            <div className="seatmap-event-info">
              <h2>{event.name}</h2>
              <span className="seatmap-venue">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" stroke="currentColor" strokeWidth="2"/>
                  <circle cx="12" cy="9" r="2.5" stroke="currentColor" strokeWidth="2"/>
                </svg>
                {event.venue}
              </span>
            </div>
          </div>

          {error && (
            <div className="alert alert--error">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.5"/>
                <path d="M12 8v4M12 16h.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
              {error}
              <button onClick={() => setError(null)} className="alert-close">×</button>
            </div>
          )}

          <div className="stats-row">
            <div className="stat-pill">
              <span className="stat-dot stat-dot--green"></span>
              <span><strong>{seatMap?.available_seats ?? 0}</strong> available</span>
            </div>
            <div className="stat-pill">
              <span className="stat-dot stat-dot--red"></span>
              <span><strong>{sold}</strong> sold</span>
            </div>
            <div className="stat-pill">
              <span><strong>{seatMap?.total_seats ?? 0}</strong> total</span>
            </div>
            {lastUpdated && (
              <span className="last-updated">Updated {lastUpdated.toLocaleTimeString()}</span>
            )}
          </div>

          <div className="legend-row">
            <div className="legend-item"><div className="seat seat--available seat--sm"></div><span>Available</span></div>
            <div className="legend-item"><div className="seat seat--selected seat--sm"></div><span>Selected</span></div>
            <div className="legend-item"><div className="seat seat--reserved seat--sm"></div><span>Reserved</span></div>
            <div className="legend-item"><div className="seat seat--sold seat--sm"></div><span>Sold</span></div>
          </div>

          <div className="stage-wrap">
            <div className="stage-label">STAGE</div>
            <div className="stage-glow"></div>
          </div>

          <div className="seat-grid">
            {sortedRowKeys.map(rowKey => (
              <div key={rowKey} className="seat-row">
                <span className="row-label">{rowKey}</span>
                <div className="row-seats">
                  {seatRows[rowKey].map(seat => (
                    <div
                      key={seat.seat_id}
                      className={getSeatClass(seat)}
                      onClick={() => handleSeatClick(seat)}
                      title={`Row ${seat.row}, Seat ${seat.number} — ${seat.status}`}
                    >
                      {seat.number}
                    </div>
                  ))}
                </div>
                <span className="row-label">{rowKey}</span>
              </div>
            ))}
          </div>

          <div className="refresh-hint">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
              <path d="M1 4v6h6M23 20v-6h-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Auto-refreshing every 5 seconds
          </div>
        </div>

        {/* Right: Booking panel */}
        <aside className="booking-panel">
          <div className="booking-panel-inner">
            <h3 className="panel-title">Your Selection</h3>

            {!selectedSeat ? (
              <div className="panel-empty">
                <div className="panel-empty-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                    <rect x="2" y="7" width="20" height="14" rx="2" stroke="currentColor" strokeWidth="1.5"/>
                    <path d="M8 7V5a4 4 0 018 0v2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  </svg>
                </div>
                <p>Click any green seat<br/>to select it</p>
              </div>
            ) : (
              <div className="panel-selected">
                <div className="selected-seat-card">
                  <div className="selected-seat-label">
                    <span className="seat-badge">Row {selectedSeat.row} · Seat {selectedSeat.number}</span>
                  </div>
                  <div className="selected-seat-section">{selectedSeat.section}</div>
                </div>

                <div className="price-breakdown">
                  <div className="price-row">
                    <span>Ticket price</span>
                    <span>${event.price}</span>
                  </div>
                  <div className="price-row price-row--total">
                    <span>Total</span>
                    <span>${event.price}</span>
                  </div>
                </div>

                <div className="panel-form">
                  <label className="input-label">
                    Email address
                    <span className="input-hint">for confirmation</span>
                  </label>
                  <input
                    type="email"
                    placeholder="you@example.com"
                    value={userEmail}
                    onChange={e => setUserEmail(e.target.value)}
                    className="panel-input"
                  />
                </div>

                <button
                  onClick={handleReservation}
                  disabled={reserving}
                  className="reserve-btn"
                >
                  {reserving ? (
                    <>
                      <div className="btn-spinner"></div>
                      Processing…
                    </>
                  ) : (
                    <>
                      Reserve Seat
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </>
                  )}
                </button>

                <button
                  onClick={() => setSelectedSeat(null)}
                  disabled={reserving}
                  className="clear-btn"
                >
                  Clear selection
                </button>

                <p className="panel-disclaimer">
                  No payment required now. Seat held for 10 minutes after reservation.
                </p>
              </div>
            )}

            <div className="panel-stats">
              <div className="mini-bar-label">
                <span>{pct}% sold</span>
                <span>{seatMap?.available_seats} remaining</span>
              </div>
              <div className="mini-bar-track">
                <div className="mini-bar-fill" style={{ width: `${pct}%` }}></div>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default SeatMap;
