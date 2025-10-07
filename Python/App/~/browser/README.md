# Custom Browser

A beautiful, modern web browser built with Flask backend and a stunning white and gradient theme frontend.

## Features

- 🎨 **Beautiful White & Gradient Theme** - Modern UI with smooth gradients and glassmorphism effects
- 🌐 **Multi-tab Browsing** - Create, manage, and switch between multiple tabs
- 📍 **Address Bar Navigation** - Smart URL handling with auto-protocol detection
- 📚 **Bookmarks System** - Save and organize your favorite websites
- 📖 **Browsing History** - Track your browsing history with easy access
- 🔄 **Real-time Updates** - WebSocket-powered real-time communication
- 📱 **Responsive Design** - Works perfectly on desktop and mobile devices
- ⚡ **Fast Performance** - Optimized for speed and efficiency

## Quick Start

### Prerequisites

- Python 3.7+
- pip (Python package installer)

### Installation

1. **Navigate to the browser directory:**
   ```bash
   cd ~/browser
   ```

2. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Run the browser:**
   ```bash
   python app.py
   ```

4. **Open your browser:**
   - Navigate to `http://localhost:5000`
   - Enjoy your custom browser!

## Usage

### Navigation
- **Address Bar**: Type any URL and press Enter to navigate
- **Navigation Buttons**: Use ← → buttons to go back/forward
- **Refresh**: Click the ↻ button to reload the current page
- **Bookmark**: Click the ★ button to save the current page

### Tab Management
- **New Tab**: Click the + button to create a new tab
- **Switch Tabs**: Click on any tab to switch to it
- **Close Tab**: Click the × button on any tab to close it

### History & Bookmarks
- **Access**: Click the ☰ button to open the sidebar
- **History**: View your recent browsing history
- **Bookmarks**: Manage your saved bookmarks
- **Quick Access**: Click on any history item or bookmark to navigate instantly

## Technical Details

### Backend (Flask)
- **Framework**: Flask with WebSocket support
- **Communication**: Real-time WebSocket communication
- **URL Fetching**: HTTP requests with proper error handling
- **State Management**: In-memory storage for tabs, history, and bookmarks

### Frontend (HTML/CSS/JavaScript)
- **Theme**: White and gradient design with glassmorphism effects
- **Responsive**: Mobile-first responsive design
- **Animations**: Smooth transitions and hover effects
- **Real-time**: WebSocket integration for live updates

### Architecture
```
~/browser/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── requirements.txt    # Python dependencies
│   └── templates/
│       └── index.html      # Browser UI
└── README.md               # This file
```

## Customization

### Changing the Theme
Edit the CSS in `backend/templates/index.html` to customize:
- Color schemes
- Gradients
- Animations
- Layout spacing

### Adding Features
Extend the browser by modifying:
- `app.py` for backend functionality
- `index.html` for frontend features
- Add new API endpoints as needed

## Browser Features

### Current Features
- ✅ URL navigation and rendering
- ✅ Multi-tab support
- ✅ Back/Forward navigation
- ✅ Bookmark management
- ✅ Browsing history
- ✅ Responsive design
- ✅ Real-time updates

### Planned Features
- 🔲 Search engine integration
- 🔲 Download manager
- 🔲 Developer tools
- 🔲 Extensions support
- 🔲 Privacy mode
- 🔲 Password manager

## Troubleshooting

### Common Issues

1. **Port already in use:**
   - Change the port in `app.py` (line with `socketio.run`)
   - Or kill the process using port 5000

2. **Dependencies not installing:**
   - Make sure you have Python 3.7+ installed
   - Try using `pip3` instead of `pip`

3. **WebSocket connection issues:**
   - Check if your firewall allows port 5000
   - Ensure no other application is using the port

## Contributing

Feel free to contribute to this project by:
- Adding new features
- Improving the UI/UX
- Fixing bugs
- Adding tests
- Improving documentation

## License

This project is open source and available under the MIT License.

---

**Enjoy browsing with your custom browser! 🚀**
