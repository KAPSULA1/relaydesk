# RelayDesk Frontend

A modern, real-time chat application built with Next.js 16, featuring a Discord/Linear-inspired design with beautiful animations and dark/light mode support.

## Features

- **Modern UI/UX**: Professional, animated interface using Framer Motion
- **Real-time Chat**: WebSocket-based instant messaging
- **Dark/Light Mode**: Persistent theme switching with Zustand
- **Responsive Design**: Mobile-first, works beautifully on all devices
- **Toast Notifications**: Animated user feedback system
- **Loading States**: Skeleton screens for better UX
- **State Management**: Zustand for global UI and chat state
- **TypeScript**: Full type safety throughout the application

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **Animations**: Framer Motion
- **State Management**: Zustand
- **Icons**: Lucide React
- **Real-time**: WebSocket with JWT authentication

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000`
- Environment variables configured in `.env.local`

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

### Build

```bash
npm run build
```

### Production

```bash
npm start
```

## Project Structure

```
frontend/
├── app/                      # Next.js App Router pages
│   ├── (auth)/login/         # Login page with animations
│   ├── rooms/                # Rooms list page
│   ├── chat/[slug]/          # Dynamic chat room page
│   └── page.tsx              # Home/redirect page
├── components/
│   └── ui/                   # Reusable UI components
│       ├── Skeleton.tsx      # Loading skeleton components
│       └── Toast.tsx         # Toast notification system
└── lib/
    ├── api/                  # API client configuration
    └── stores/               # Zustand state management
        ├── uiStore.ts        # UI state (theme, notifications)
        └── chatStore.ts      # Chat state (messages, typing)
```

## Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_HOST=localhost:8000
NEXT_PUBLIC_APP_NAME=RelayDesk
```

## Demo Accounts

- Username: `alice_dev` / Password: `demo123`
- Username: `bob_designer` / Password: `demo123`

## Key Features Implemented

### Authentication
- JWT-based authentication
- Persistent login state
- Animated login page with validation

### Chat Interface
- Real-time message delivery via WebSockets
- Animated message bubbles with avatars
- Typing indicators
- Online/offline status with pulsing dots
- Message timestamps
- Auto-scroll to latest messages

### Rooms Page
- Grid layout with room cards
- Search functionality
- Room statistics (message count)
- Animated hover effects
- Empty states

### UI Components
- Toast notifications with auto-dismiss
- Loading skeletons for better perceived performance
- Theme toggle with persistence
- Responsive navigation
- Gradient buttons with animations

## Performance Optimizations

- Static page generation where possible
- Dynamic imports for heavy components
- Optimized WebSocket connections
- Efficient state updates with Zustand
- CSS animations via Framer Motion (GPU accelerated)

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

## Contributing

This is a portfolio project showcasing modern web development practices. Feel free to explore and learn from the codebase!
