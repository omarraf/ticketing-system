# Event Ticketing System - Frontend

React frontend for the high-concurrency event ticketing system.

## Features

- **Event Listing**: Browse all available events with real-time seat counts
- **Interactive Seat Map**: Visual seat selection with row/column layout
- **Real-time Updates**: Seat availability refreshes every 5 seconds
- **Booking Flow**: Complete reservation process with confirmation
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Visual Feedback**: Loading states, error handling, and success confirmations

## Technology Stack

- **React 18** - UI framework
- **Axios** - HTTP client for API communication
- **CSS3** - Modern styling with animations and gradients
- **React Hooks** - useState, useEffect for state management

## Setup

### Prerequisites

- Node.js 16+ and npm

### Installation

```bash
# Install dependencies
npm install
```

### Configuration

1. Copy the environment example file:
```bash
cp .env.example .env
```

2. Update `.env` with your API Gateway URL (from Terraform outputs):
```bash
REACT_APP_API_URL=https://your-api-id.execute-api.us-east-1.amazonaws.com
```

## Development

### Start Development Server

```bash
npm start
```

The app will open at http://localhost:3000

Changes will hot-reload automatically.

### Build for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` folder.

## Project Structure

```
frontend/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── components/
│   │   ├── EventList.js        # Event listing component
│   │   ├── SeatMap.js          # Interactive seat selection
│   │   └── BookingConfirmation.js  # Success confirmation
│   ├── services/
│   │   └── api.js              # API client
│   ├── styles/
│   │   ├── App.css
│   │   ├── EventList.css
│   │   ├── SeatMap.css
│   │   └── BookingConfirmation.css
│   ├── App.js              # Main app component
│   └── index.js            # React entry point
├── package.json
└── README.md
```

## Components

### EventList
- Displays all available events
- Shows seat availability and pricing
- Filters sold-out events
- Auto-refresh capability

### SeatMap
- Interactive seat grid organized by rows
- Real-time availability updates (5s interval)
- Visual seat status (available, reserved, sold)
- Email collection for confirmations
- Concurrent booking protection

### BookingConfirmation
- Success message and booking details
- Payment status indicator
- Next steps information
- Booking ID for reference

## API Integration

The frontend communicates with the Lambda backend via API Gateway:

- `GET /events` - Fetch all events
- `GET /events/{event_id}/seats` - Get seat map for an event
- `POST /reserve` - Reserve a seat

All API calls are made through the centralized `api.js` service with:
- Error handling
- Request/response logging
- Timeout configuration
- CORS support

## Deployment Options

### Option 1: S3 + CloudFront (Recommended)

```bash
# Build production bundle
npm run build

# Upload to S3 bucket (configure AWS CLI first)
aws s3 sync build/ s3://your-bucket-name --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### Option 2: Netlify

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
npm run build
netlify deploy --prod --dir=build
```

### Option 3: Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel --prod
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `REACT_APP_API_URL` | API Gateway endpoint | `https://abc123.execute-api.us-east-1.amazonaws.com` |

## Features Demonstrated

### Concurrent Booking Prevention
- Optimistic UI updates
- Real-time seat status refresh
- Error handling for double-booking attempts
- Visual feedback during reservation

### User Experience
- Loading states with spinners
- Error messages with retry options
- Success confirmations
- Responsive mobile design
- Smooth animations and transitions

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

- Lazy loading for components
- Efficient re-rendering with React hooks
- Optimized bundle size (~200KB gzipped)
- Fast page loads with code splitting

## Troubleshooting

### API Connection Issues

If you see CORS errors:
1. Verify API Gateway CORS is configured in Lambda responses
2. Check that `REACT_APP_API_URL` is correct
3. Ensure API Gateway is deployed

### Seats Not Updating

If seat availability doesn't refresh:
1. Check browser console for API errors
2. Verify backend Lambda functions are deployed
3. Check DynamoDB tables have data

## Future Enhancements

- [ ] User authentication (AWS Cognito)
- [ ] Payment integration (Stripe)
- [ ] Booking history
- [ ] Email notifications
- [ ] Seat filtering by section/price
- [ ] Multi-event cart
- [ ] WebSocket for real-time updates

## License

MIT
