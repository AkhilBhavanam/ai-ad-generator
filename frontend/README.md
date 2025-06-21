# VideoAI - URL to Video AI Platform Frontend

A modern, responsive React application built specifically for the **URL-to-Video AI Platform**. Transform any e-commerce product URL into compelling video advertisements using AI-powered scraping, script generation, and video creation.

## 🚀 Platform Overview

This frontend provides a beautiful, intuitive interface for your URL-to-Video AI backend that can:

- 🔗 **Extract product data** from e-commerce URLs (eBay, Shopify, Etsy, Amazon, etc.)
- 🤖 **Generate AI-powered ad scripts** using OpenAI
- 🎬 **Create professional video advertisements** with:
  - Multiple aspect ratios (16:9, 9:16, 1:1, 4:3)
  - AI voiceover using ElevenLabs
  - Karaoke-style text animations
  - Professional templates and styling

## ✨ Features

### 🎨 Modern UI/UX
- **Beautiful gradient design** with purple/blue theme
- **Responsive layout** that works on all devices
- **Smooth animations** and hover effects throughout
- **Toast notifications** for elegant user feedback
- **Progress tracking** with visual indicators

### 🛠️ Core Components

#### 1. **Hero Section**
- Compelling landing page with feature highlights
- Sample URL examples for eBay, Shopify, Etsy
- Platform badges with scraping-friendly recommendations
- Clear call-to-action buttons

#### 2. **Video Generator Workflow**
- **Step 1: URL Input** - Validate and analyze product URLs
- **Step 2: Settings** - Configure video parameters
- **Step 3: Generation** - Real-time progress tracking
- **Step 4: Results** - Preview and download generated videos

#### 3. **Advanced Settings Panel**
- **Aspect Ratios**: 16:9, 9:16, 1:1, 4:3
- **Templates**: Modern, Dynamic, Minimalist, Professional
- **Voice Options**: Professional, Exciting, Friendly, Calm
- **Features**: Karaoke text, AI voiceover toggles

#### 4. **Results Display**
- **Video Preview** with playback controls
- **Product Information** display with images and details
- **AI Script Preview** showing hook, problem, solution, CTA
- **Download and sharing** functionality

### 🎯 Smart Features

#### URL Validation
- Automatic platform detection
- Support for major e-commerce sites
- Helpful error messages and suggestions

#### Progress Tracking
- Real-time generation status
- Visual progress indicators
- Detailed step descriptions

#### Responsive Design
- Mobile-first approach
- Tablet and desktop optimization
- Touch-friendly interactions

## 🛠️ Technology Stack

- **React 18** - Latest version with concurrent features
- **Tailwind CSS** - Utility-first CSS framework with custom design system
- **Vite** - Fast build tool and dev server
- **Modern JavaScript** - ES6+ features and async/await
- **Component Architecture** - Modular, reusable components

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Header.jsx              # Navigation with VideoAI branding
│   │   ├── Hero.jsx                # Landing page with features
│   │   ├── VideoGenerator.jsx      # Main workflow orchestrator
│   │   ├── UrlInput.jsx            # URL input with validation
│   │   ├── VideoSettings.jsx       # Settings configuration
│   │   ├── GenerationProgress.jsx  # Progress tracking
│   │   ├── ProductPreview.jsx      # Scraped product display
│   │   ├── ScriptPreview.jsx       # AI script display
│   │   ├── VideoPreview.jsx        # Generated video player
│   │   ├── ToastProvider.jsx       # Notification system
│   │   └── Footer.jsx              # Platform-specific footer
│   ├── App.jsx                     # Main app component
│   ├── main.jsx                    # React entry point
│   └── index.css                   # Custom Tailwind styles
├── public/
│   ├── index.html                  # HTML template
│   └── vite.svg                    # Vite icon
├── package.json                    # Dependencies and scripts
├── tailwind.config.js              # Tailwind configuration
├── postcss.config.js               # PostCSS configuration
├── vite.config.js                  # Vite build configuration
└── README.md                       # This file
```

## 🎨 Design System

### Colors
- **Primary**: Purple gradient (`#a855f7` to `#3b82f6`)
- **Success**: Green (`#10b981`)
- **Error**: Red (`#ef4444`)
- **Warning**: Yellow (`#f59e0b`)
- **Gray Scale**: Modern gray palette

### Components
- **Buttons**: Gradient primary, subtle secondary
- **Cards**: Elevated with hover effects
- **Forms**: Clean inputs with focus states
- **Notifications**: Contextual toast messages

### Animations
- **Hover effects**: Scale and shadow transforms
- **Loading states**: Pulse and spin animations
- **Transitions**: Smooth color and transform changes

## 🚀 Getting Started

### Prerequisites
- **Node.js** (version 18 or higher)
- **npm** (comes with Node.js)

### Installation

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Visit `http://localhost:3000`

### Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint for code quality

## 🔌 Backend Integration

This frontend is designed to work with your Python FastAPI backend:

### API Endpoints Used
- `POST /api/generate-video` - Main video generation endpoint
- `POST /api/scrape` - Product data scraping
- `GET /api/download/{session_id}` - Video download
- `GET /api/status/{session_id}` - Generation status

### Data Flow
1. **URL Submission** → Validation and platform detection
2. **Settings Configuration** → Aspect ratio, template, voice options
3. **Generation Request** → POST to `/api/generate-video`
4. **Progress Tracking** → Real-time status updates
5. **Results Display** → Product data, script, and video preview

## 🎯 Key Features Integration

### Supported Platforms
- **eBay** - Recommended platform with scraping-friendly policies
- **Shopify** - Store product information
- **Etsy** - Handmade product details
- **Amazon** - Limited support due to anti-bot protection
- **Generic Sites** - Fallback scraping

### AI Integration
- **OpenAI Script Generation** - Hooks, problems, solutions, CTAs
- **ElevenLabs Voiceover** - Professional AI voices
- **Multiple Tones** - Professional, exciting, friendly, calm

### Video Features
- **Multiple Formats** - 16:9, 9:16, 1:1, 4:3
- **Professional Templates** - Modern, dynamic, minimalist
- **Karaoke Text** - Word-by-word highlighting
- **Background Music** - Corporate audio tracks

## 🔧 Customization

### Theming
The design system is built with Tailwind CSS and can be easily customized:

```javascript
// tailwind.config.js
theme: {
  extend: {
    colors: {
      primary: {
        500: '#your-color',
        600: '#your-darker-color',
      }
    }
  }
}
```

### Components
All components are modular and can be easily modified or extended:

```jsx
// Example: Custom button component
const CustomButton = ({ children, variant = 'primary', ...props }) => {
  return (
    <button className={`btn btn-${variant}`} {...props}>
      {children}
    </button>
  )
}
```

## 📱 Responsive Design

The application is fully responsive with breakpoints:
- **Mobile**: < 640px
- **Tablet**: 640px - 1024px  
- **Desktop**: > 1024px

All components adapt gracefully across devices with:
- Mobile-first CSS approach
- Touch-friendly interactions
- Optimized layouts for each screen size

## 🚀 Deployment

### Build for Production
```bash
npm run build
```

### Deploy Options
- **Vercel** - Zero-config deployment
- **Netlify** - Static site hosting
- **AWS S3 + CloudFront** - Enterprise hosting
- **Docker** - Containerized deployment

### Environment Variables
Create a `.env` file for environment-specific settings:
```env
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=VideoAI
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

**Transform any URL into engaging video content with AI! 🎬✨** 