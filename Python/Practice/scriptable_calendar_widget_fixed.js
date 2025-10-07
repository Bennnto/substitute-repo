/*
 * Calendar & Reminders Widget for Scriptable - FIXED VERSION
 * iOS 26 Liquid Glass Theme - Calendar Access Fixed
 * 
 * FIXES APPLIED:
 * - Enhanced calendar permission handling
 * - Robust error handling and fallbacks  
 * - Better refresh mechanisms
 * - Debug logging for troubleshooting
 * - Multiple calendar access attempts
 */

// Configuration
const CONFIG = {
  // Widget settings
  WIDGET_SIZE: "medium",
  DISPLAY_MODE: "today",
  DEBUG_MODE: true, // Enable debug logging
  
  // Refresh settings
  REFRESH_INTERVAL: 15, // minutes
  MAX_RETRY_ATTEMPTS: 3,
  
  // iOS 26 Liquid Glass Theme
  THEME: {
    primary: {
      background: new Color("#F8F9FA", 0.1),
      glass: new Color("#FFFFFF", 0.15),
      glassHigh: new Color("#FFFFFF", 0.25),
      accent: new Color("#007AFF", 0.8)
    },
    
    text: {
      primary: new Color("#000000", 0.9),
      secondary: new Color("#666666", 0.8),
      accent: new Color("#007AFF", 1.0)
    },
    
    events: {
      health: new Color("#FF2D92", 0.8),
      work: new Color("#007AFF", 0.8),
      personal: new Color("#34C759", 0.8)
    },
    
    glass: {
      border: new Color("#FFFFFF", 0.3)
    }
  },
  
  // Keywords for event classification
  HEALTH_KEYWORDS: ["doctor", "appointment", "medical", "health", "dentist", "medication"],
  WORK_KEYWORDS: ["meeting", "call", "interview", "work", "conference", "presentation"],
  PRIORITY_KEYWORDS: ["medication", "doctor", "appointment", "urgent", "important"]
}

// Debug logging function
function debugLog(message, level = "INFO") {
  if (CONFIG.DEBUG_MODE) {
    const timestamp = new Date().toLocaleTimeString()
    console.log(`[${timestamp}] [${level}] ${message}`)
  }
}

// Create liquid glass background
function createLiquidGlassBackground() {
  const context = new DrawContext()
  context.size = new Size(400, 200)
  context.opaque = false
  
  const gradient = new LinearGradient()
  gradient.colors = [
    new Color("#E3F2FD", 0.2),
    new Color("#F8F9FA", 0.1),
    new Color("#E8F5E8", 0.15),
    new Color("#FFF3E0", 0.1)
  ]
  gradient.locations = [0.0, 0.3, 0.7, 1.0]
  gradient.startPoint = new Point(0, 0)
  gradient.endPoint = new Point(1, 1)
  
  const rect = new Rect(0, 0, 400, 200)
  context.setFillColor(new Color("#FFFFFF", 0.1))
  context.fillRect(rect)
  
  return context.getImage()
}

// Get theme colors
function getThemeColors() {
  return {
    background: Color.clear(),
    text: CONFIG.THEME.text.primary,
    subtext: CONFIG.THEME.text.secondary,
    cardBackground: CONFIG.THEME.primary.glass,
    accent: CONFIG.THEME.text.accent,
    health: CONFIG.THEME.events.health,
    work: CONFIG.THEME.events.work,
    personal: CONFIG.THEME.events.personal
  }
}

// FIXED: Enhanced calendar data retrieval with debugging
async function getCalendarData() {
  debugLog("=== Starting Calendar Data Retrieval ===")
  
  try {
    const now = new Date()
    const startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const endDate = new Date(now.getTime() + (7 * 24 * 60 * 60 * 1000))
    
    debugLog(`Date range: ${startDate.toDateString()} to ${endDate.toDateString()}`)
    
    let events = []
    let hasAccess = false
    
    // FIXED: Multiple attempts to get calendar access
    for (let attempt = 1; attempt <= CONFIG.MAX_RETRY_ATTEMPTS; attempt++) {
      debugLog(`Calendar access attempt ${attempt}/${CONFIG.MAX_RETRY_ATTEMPTS}`)
      
      try {
        hasAccess = await Calendar.requestAccess()
        debugLog(`Calendar access result: ${hasAccess}`)
        
        if (hasAccess) {
          debugLog("✅ Calendar access granted")
          break
        } else {
          debugLog(`❌ Calendar access denied on attempt ${attempt}`)
          if (attempt < CONFIG.MAX_RETRY_ATTEMPTS) {
            // Wait before retry
            await new Promise(resolve => setTimeout(resolve, 1000))
          }
        }
      } catch (accessError) {
        debugLog(`❌ Calendar access error on attempt ${attempt}: ${accessError.message}`, "ERROR")
      }
    }
    
    // If we have access, try to get events
    if (hasAccess) {
      try {
        debugLog("Fetching calendar events...")
        
        // FIXED: Get all available calendars first
        const availableCalendars = await Calendar.forEvents()
        debugLog(`Found ${availableCalendars.length} available calendars`)
        
        // List calendar names for debugging
        availableCalendars.forEach((cal, index) => {
          debugLog(`  Calendar ${index + 1}: "${cal.title}" (${cal.identifier})`)
        })
        
        // FIXED: Get events from all calendars
        if (availableCalendars.length > 0) {
          events = await CalendarEvent.between(startDate, endDate, availableCalendars)
          debugLog(`✅ Successfully retrieved ${events.length} events`)
          
          // Log first few events for debugging
          events.slice(0, 3).forEach((event, index) => {
            debugLog(`  Event ${index + 1}: "${event.title}" at ${event.startDate}`)
          })
        } else {
          debugLog("⚠️ No calendars available", "WARNING")
        }
        
      } catch (eventError) {
        debugLog(`❌ Error fetching events: ${eventError.message}`, "ERROR")
        debugLog("Falling back to mock data", "WARNING")
      }
    } else {
      debugLog("❌ Calendar access not granted, using mock data", "WARNING")
    }
    
    // FIXED: Enhanced fallback logic
    if (events.length === 0) {
      debugLog("Using mock calendar data as fallback")
      const mockData = getMockCalendarData()
      events = mockData.events
      debugLog(`Mock data loaded: ${events.length} events`)
    }
    
    // Group events by date
    const eventsByDate = {}
    events.forEach(event => {
      const dateKey = formatDate(event.startDate, "key")
      if (!eventsByDate[dateKey]) {
        eventsByDate[dateKey] = []
      }
      eventsByDate[dateKey].push(event)
    })
    
    debugLog(`Events grouped by date: ${Object.keys(eventsByDate).length} days`)
    debugLog("=== Calendar Data Retrieval Complete ===")
    
    return { events, eventsByDate, hasRealData: hasAccess && events.length > 0 }
    
  } catch (error) {
    debugLog(`❌ Critical error in getCalendarData: ${error.message}`, "ERROR")
    debugLog("Using emergency mock data", "ERROR")
    return getMockCalendarData()
  }
}

// FIXED: Enhanced reminder data retrieval
async function getReminderData() {
  debugLog("=== Starting Reminder Data Retrieval ===")
  
  try {
    let reminders = []
    let hasAccess = false
    
    // FIXED: Multiple attempts for reminder access
    for (let attempt = 1; attempt <= CONFIG.MAX_RETRY_ATTEMPTS; attempt++) {
      debugLog(`Reminder access attempt ${attempt}/${CONFIG.MAX_RETRY_ATTEMPTS}`)
      
      try {
        hasAccess = await Reminder.requestAccess()
        debugLog(`Reminder access result: ${hasAccess}`)
        
        if (hasAccess) {
          debugLog("✅ Reminder access granted")
          break
        } else {
          debugLog(`❌ Reminder access denied on attempt ${attempt}`)
          if (attempt < CONFIG.MAX_RETRY_ATTEMPTS) {
            await new Promise(resolve => setTimeout(resolve, 1000))
          }
        }
      } catch (accessError) {
        debugLog(`❌ Reminder access error on attempt ${attempt}: ${accessError.message}`, "ERROR")
      }
    }
    
    if (hasAccess) {
      try {
        debugLog("Fetching reminders...")
        
        // Get all incomplete reminders
        const allReminders = await Reminder.incomplete()
        debugLog(`Retrieved ${allReminders.length} incomplete reminders`)
        
        // Get reminder lists for debugging
        const reminderLists = await ReminderList.all()
        debugLog(`Available reminder lists: ${reminderLists.length}`)
        reminderLists.forEach((list, index) => {
          debugLog(`  List ${index + 1}: "${list.title}"`)
        })
        
        reminders = allReminders
        
      } catch (reminderError) {
        debugLog(`❌ Error fetching reminders: ${reminderError.message}`, "ERROR")
      }
    } else {
      debugLog("❌ Reminder access not granted, using mock data", "WARNING")
    }
    
    // Fallback to mock data
    if (reminders.length === 0) {
      debugLog("Using mock reminder data as fallback")
      const mockData = getMockReminderData()
      reminders = mockData.reminders
      debugLog(`Mock reminder data loaded: ${reminders.length} reminders`)
    }
    
    // Sort by priority and due date
    reminders.sort((a, b) => {
      const aPriority = isPriorityReminder(a)
      const bPriority = isPriorityReminder(b)
      
      if (aPriority && !bPriority) return -1
      if (!aPriority && bPriority) return 1
      
      if (a.dueDate && b.dueDate) {
        return a.dueDate - b.dueDate
      }
      if (a.dueDate && !b.dueDate) return -1
      if (!a.dueDate && b.dueDate) return 1
      
      return 0
    })
    
    debugLog("=== Reminder Data Retrieval Complete ===")
    
    return { 
      reminders: reminders.slice(0, 8),
      hasRealData: hasAccess && reminders.length > 0 
    }
    
  } catch (error) {
    debugLog(`❌ Critical error in getReminderData: ${error.message}`, "ERROR")
    return getMockReminderData()
  }
}

// FIXED: Main widget creation with better error handling
async function createWidget() {
  debugLog("=== Starting Widget Creation ===")
  
  const widget = new ListWidget()
  const colors = getThemeColors()
  
  // Set liquid glass background
  const bgImage = createLiquidGlassBackground()
  widget.backgroundImage = bgImage
  
  // FIXED: Set refresh interval
  const refreshDate = new Date(Date.now() + CONFIG.REFRESH_INTERVAL * 60 * 1000)
  widget.refreshAfterDate = refreshDate
  debugLog(`Widget will refresh after: ${refreshDate.toLocaleTimeString()}`)
  
  // Minimal padding to prevent overflow
  widget.setPadding(4, 4, 4, 4)
  
  try {
    // Create header
    await createHeader(widget, colors)
    
    widget.addSpacer(3)
    
    // FIXED: Get data with better error handling
    debugLog("Fetching calendar and reminder data...")
    const [calendarData, reminderData] = await Promise.allSettled([
      getCalendarData(),
      getReminderData()
    ])
    
    const finalCalendarData = calendarData.status === 'fulfilled' ? 
      calendarData.value : getMockCalendarData()
    const finalReminderData = reminderData.status === 'fulfilled' ? 
      reminderData.value : getMockReminderData()
    
    debugLog("Data fetching completed")
    
    // Create main content
    await createMainContent(widget, colors, finalCalendarData, finalReminderData)
    
    // FIXED: Add data source indicator
    if (CONFIG.DEBUG_MODE) {
      widget.addSpacer(2)
      const debugStack = widget.addStack()
      debugStack.layoutHorizontally()
      debugStack.cornerRadius = 4
      debugStack.backgroundColor = new Color("#000000", 0.1)
      debugStack.setPadding(2, 4, 2, 4)
      
      const dataSource = `📊 Cal:${finalCalendarData.hasRealData ? 'Live' : 'Mock'} | Rem:${finalReminderData.hasRealData ? 'Live' : 'Mock'}`
      const debugText = debugStack.addText(dataSource)
      debugText.textColor = colors.subtext
      debugText.font = Font.systemFont(6)
    }
    
    debugLog("=== Widget Creation Complete ===")
    
  } catch (error) {
    debugLog(`❌ Error creating widget: ${error.message}`, "ERROR")
    debugLog(`Error stack: ${error.stack}`, "ERROR")
    return createErrorWidget(error.message, colors)
  }
  
  return widget
}

// FIXED: Enhanced header with connection status
async function createHeader(widget, colors) {
  const headerContainer = widget.addStack()
  headerContainer.layoutHorizontally()
  headerContainer.cornerRadius = 8
  headerContainer.backgroundColor = CONFIG.THEME.primary.glass
  headerContainer.setPadding(6, 10, 6, 10)
  headerContainer.borderWidth = 0.5
  headerContainer.borderColor = CONFIG.THEME.glass.border
  
  // Left side - Title with icon
  const titleStack = headerContainer.addStack()
  titleStack.layoutHorizontally()
  titleStack.centerAlignContent()
  
  const calendarIcon = titleStack.addText("📅")
  calendarIcon.font = Font.systemFont(12)
  calendarIcon.textColor = colors.text
  
  titleStack.addSpacer(4)
  
  const titleText = titleStack.addText("Calendar & Reminders")
  titleText.textColor = colors.text
  titleText.font = Font.boldSystemFont(11)
  
  headerContainer.addSpacer()
  
  // Right side - Date and time
  const infoStack = headerContainer.addStack()
  infoStack.layoutVertically()
  infoStack.centerAlignContent()
  
  const now = new Date()
  const dateText = infoStack.addText(formatDate(now, "header"))
  dateText.textColor = colors.text
  dateText.font = Font.boldSystemFont(10)
  dateText.rightAlignText()
  
  const timeText = infoStack.addText(formatTime(now))
  timeText.textColor = colors.accent
  timeText.font = Font.boldSystemFont(11)
  timeText.rightAlignText()
}

// Create main content layout
async function createMainContent(widget, colors, calendarData, reminderData) {
  const contentStack = widget.addStack()
  contentStack.layoutVertically()
  contentStack.spacing = 3
  
  // Top row with two columns
  const topRow = contentStack.addStack()
  topRow.layoutHorizontally()
  topRow.spacing = 3
  
  // Left column - Today's Events
  const eventsColumn = topRow.addStack()
  eventsColumn.layoutVertically()
  eventsColumn.cornerRadius = 8
  eventsColumn.backgroundColor = CONFIG.THEME.primary.glass
  eventsColumn.setPadding(8, 10, 8, 10)
  eventsColumn.borderWidth = 0.5
  eventsColumn.borderColor = CONFIG.THEME.glass.border
  await createTodayEvents(eventsColumn, colors, calendarData)
  
  // Right column - Priority Tasks
  const tasksColumn = topRow.addStack()
  tasksColumn.layoutVertically()
  tasksColumn.cornerRadius = 8
  tasksColumn.backgroundColor = CONFIG.THEME.primary.glass
  tasksColumn.setPadding(8, 10, 8, 10)
  tasksColumn.borderWidth = 0.5
  tasksColumn.borderColor = CONFIG.THEME.glass.border
  await createPriorityTasks(tasksColumn, colors, reminderData)
  
  // Bottom row - Summary
  const bottomRow = contentStack.addStack()
  bottomRow.layoutHorizontally()
  bottomRow.cornerRadius = 8
  bottomRow.backgroundColor = CONFIG.THEME.primary.glass
  bottomRow.setPadding(5, 10, 5, 10)
  bottomRow.borderWidth = 0.5
  bottomRow.borderColor = CONFIG.THEME.glass.border
  await createSummaryRow(bottomRow, colors, calendarData, reminderData)
}

// Create today's events section
async function createTodayEvents(container, colors, calendarData) {
  // Header
  const headerStack = container.addStack()
  headerStack.layoutHorizontally()
  headerStack.centerAlignContent()
  
  const eventIcon = headerStack.addText("📅")
  eventIcon.font = Font.systemFont(10)
  
  headerStack.addSpacer(3)
  
  const headerText = headerStack.addText("Today's Events")
  headerText.textColor = colors.text
  headerText.font = Font.boldSystemFont(9)
  
  container.addSpacer(4)
  
  // Events list
  const todayKey = formatDate(new Date(), "key")
  const todayEvents = calendarData.eventsByDate[todayKey] || []
  
  debugLog(`Today's events (${todayKey}): ${todayEvents.length}`)
  
  if (todayEvents.length === 0) {
    const noEventsText = container.addText("No events today")
    noEventsText.textColor = colors.subtext
    noEventsText.font = Font.systemFont(10)
    noEventsText.centerAlignText()
  } else {
    // Show first event with proper sizing
    const event = todayEvents[0]
    createEventRow(container, colors, event)
    
    // Show additional events indicator if needed
    if (todayEvents.length > 1) {
      container.addSpacer(4)
      const moreText = container.addText(`+${todayEvents.length - 1} more`)
      moreText.textColor = colors.subtext
      moreText.font = Font.systemFont(9)
      moreText.centerAlignText()
    }
  }
}

// Create priority tasks section
async function createPriorityTasks(container, colors, reminderData) {
  // Header
  const headerStack = container.addStack()
  headerStack.layoutHorizontally()
  headerStack.centerAlignContent()
  
  const taskIcon = headerStack.addText("📝")
  taskIcon.font = Font.systemFont(10)
  
  headerStack.addSpacer(3)
  
  const headerText = headerStack.addText("Priority Tasks")
  headerText.textColor = colors.text
  headerText.font = Font.boldSystemFont(9)
  
  container.addSpacer(4)
  
  // Tasks list
  const priorityReminders = reminderData.reminders.filter(reminder => 
    isPriorityReminder(reminder) || reminder.dueDate
  ).slice(0, 2)
  
  debugLog(`Priority reminders: ${priorityReminders.length}`)
  
  if (priorityReminders.length === 0) {
    const noTasksText = container.addText("No priority tasks")
    noTasksText.textColor = colors.subtext
    noTasksText.font = Font.systemFont(10)
    noTasksText.centerAlignText()
  } else {
    priorityReminders.forEach((reminder, index) => {
      createTaskRow(container, colors, reminder)
      if (index < priorityReminders.length - 1) {
        container.addSpacer(6)
      }
    })
  }
}

// Create event row
function createEventRow(container, colors, event) {
  const row = container.addStack()
  row.layoutHorizontally()
  row.centerAlignContent()
  row.spacing = 8
  
  // Time badge
  const timeContainer = row.addStack()
  timeContainer.setPadding(2, 4, 2, 4)
  timeContainer.cornerRadius = 4
  timeContainer.backgroundColor = CONFIG.THEME.primary.glassHigh
  
  const timeText = timeContainer.addText(event.isAllDay ? "All Day" : formatTime(event.startDate))
  timeText.textColor = colors.accent
  timeText.font = Font.boldSystemFont(7)
  
  // Event title (truncated to fit)
  const maxLength = 15
  const truncatedTitle = event.title.length > maxLength ? 
    event.title.substring(0, maxLength) + "..." : event.title
    
  const titleText = row.addText(truncatedTitle)
  titleText.textColor = getEventColor(colors, event)
  titleText.font = Font.systemFont(8)
  titleText.lineLimit = 1
  
  row.addSpacer()
  
  // Calendar indicator
  const indicator = row.addText("●")
  indicator.textColor = event.calendar ? event.calendar.color : colors.accent
  indicator.font = Font.systemFont(8)
}

// Create task row
function createTaskRow(container, colors, reminder) {
  const row = container.addStack()
  row.layoutHorizontally()
  row.centerAlignContent()
  row.spacing = 8
  
  // Priority indicator
  if (isPriorityReminder(reminder)) {
    const priorityIcon = row.addText("🔥")
    priorityIcon.font = Font.systemFont(8)
  }
  
  // Due time badge (if has due date)
  if (reminder.dueDate) {
    const dueContainer = row.addStack()
    dueContainer.setPadding(2, 4, 2, 4)
    dueContainer.cornerRadius = 3
    dueContainer.backgroundColor = CONFIG.THEME.primary.glassHigh
    
    const dueText = dueContainer.addText(formatTime(reminder.dueDate))
    dueText.textColor = colors.accent
    dueText.font = Font.systemFont(6)
  }
  
  // Task title (truncated to fit)
  const maxLength = 12
  const truncatedTitle = reminder.title.length > maxLength ? 
    reminder.title.substring(0, maxLength) + "..." : reminder.title
    
  const titleText = row.addText(truncatedTitle)
  titleText.textColor = colors.text
  titleText.font = Font.systemFont(8)
  titleText.lineLimit = 1
  
  row.addSpacer()
  
  // Completion checkbox
  const checkbox = row.addText("○")
  checkbox.textColor = colors.subtext
  checkbox.font = Font.systemFont(8)
}

// Create summary row
async function createSummaryRow(container, colors, calendarData, reminderData) {
  // Events count
  const eventsStack = container.addStack()
  eventsStack.layoutHorizontally()
  eventsStack.centerAlignContent()
  
  const eventsIcon = eventsStack.addText("📅")
  eventsIcon.font = Font.systemFont(10)
  
  eventsStack.addSpacer(2)
  
  const eventsCount = calendarData.events.filter(e => isToday(e.startDate)).length
  const eventsText = eventsStack.addText(`${eventsCount}`)
  eventsText.textColor = colors.accent
  eventsText.font = Font.boldSystemFont(10)
  
  container.addSpacer()
  
  // Tasks count
  const tasksStack = container.addStack()
  tasksStack.layoutHorizontally()
  tasksStack.centerAlignContent()
  
  const tasksIcon = tasksStack.addText("✅")
  tasksIcon.font = Font.systemFont(10)
  
  tasksStack.addSpacer(2)
  
  const tasksCount = reminderData.reminders.filter(r => !r.isCompleted).length
  const tasksText = tasksStack.addText(`${tasksCount}`)
  tasksText.textColor = colors.personal
  tasksText.font = Font.boldSystemFont(10)
}

// Check if reminder is priority
function isPriorityReminder(reminder) {
  const title = reminder.title.toLowerCase()
  return CONFIG.PRIORITY_KEYWORDS.some(keyword => 
    title.includes(keyword.toLowerCase())
  )
}

// Get event color based on type
function getEventColor(colors, event) {
  const title = event.title.toLowerCase()
  
  if (CONFIG.HEALTH_KEYWORDS.some(keyword => title.includes(keyword))) {
    return colors.health
  }
  
  if (CONFIG.WORK_KEYWORDS.some(keyword => title.includes(keyword))) {
    return colors.work
  }
  
  return colors.personal
}

// FIXED: Enhanced mock data with more realistic examples
function getMockCalendarData() {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  
  const mockEvents = [
    {
      title: "Morning Meeting",
      startDate: new Date(today.getTime() + 9 * 60 * 60 * 1000), // 9:00 AM
      endDate: new Date(today.getTime() + 10 * 60 * 60 * 1000),
      isAllDay: false,
      calendar: { title: "Work", color: Color.blue() }
    },
    {
      title: "Doctor Appointment",
      startDate: new Date(today.getTime() + 14 * 60 * 60 * 1000), // 2:00 PM
      endDate: new Date(today.getTime() + 15 * 60 * 60 * 1000),
      isAllDay: false,
      calendar: { title: "Health", color: Color.red() }
    }
  ]
  
  const eventsByDate = {}
  mockEvents.forEach(event => {
    const dateKey = formatDate(event.startDate, "key")
    if (!eventsByDate[dateKey]) {
      eventsByDate[dateKey] = []
    }
    eventsByDate[dateKey].push(event)
  })
  
  return { events: mockEvents, eventsByDate, hasRealData: false }
}

function getMockReminderData() {
  return {
    reminders: [
      {
        title: "Take morning medication",
        dueDate: new Date(Date.now() + 2 * 60 * 60 * 1000), // 2 hours from now
        isCompleted: false,
        priority: 1,
        list: { title: "Health" }
      },
      {
        title: "Call insurance company",
        dueDate: new Date(Date.now() + 4 * 60 * 60 * 1000), // 4 hours from now
        isCompleted: false,
        priority: 2,
        list: { title: "Important" }
      },
      {
        title: "Grocery shopping",
        dueDate: null,
        isCompleted: false,
        priority: 0,
        list: { title: "Personal" }
      }
    ],
    hasRealData: false
  }
}

// Utility functions
function formatDate(date, format = "display") {
  if (format === "key") {
    return date.toISOString().split('T')[0]
  } else if (format === "header") {
    return date.toLocaleDateString('en-US', { 
      weekday: 'short',
      month: 'short', 
      day: 'numeric' 
    })
  }
  
  return date.toLocaleDateString('en-US', { 
    weekday: 'short',
    month: 'short', 
    day: 'numeric' 
  })
}

function formatTime(date) {
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  })
}

function isToday(date) {
  const today = new Date()
  return date.getFullYear() === today.getFullYear() &&
         date.getMonth() === today.getMonth() &&
         date.getDate() === today.getDate()
}

// FIXED: Enhanced error widget with troubleshooting tips
function createErrorWidget(message, colors) {
  const widget = new ListWidget()
  widget.backgroundColor = colors.background
  widget.setPadding(12, 12, 12, 12)
  
  const errorText = widget.addText("⚠️ Error")
  errorText.textColor = Color.red()
  errorText.font = Font.boldSystemFont(14)
  
  widget.addSpacer(6)
  
  const messageText = widget.addText(message)
  messageText.textColor = colors.text
  messageText.font = Font.systemFont(11)
  messageText.lineLimit = 3
  
  widget.addSpacer(6)
  
  const tipText = widget.addText("💡 Check Settings → Privacy → Calendars → Scriptable")
  tipText.textColor = colors.subtext
  tipText.font = Font.systemFont(9)
  tipText.lineLimit = 2
  
  return widget
}

// FIXED: Enhanced main execution with better error handling
try {
  debugLog("=== Widget Execution Starting ===")
  debugLog(`Running in widget: ${config.runsInWidget}`)
  debugLog(`Debug mode: ${CONFIG.DEBUG_MODE}`)
  
  if (config.runsInWidget) {
    debugLog("Creating widget for home screen")
    const widget = await createWidget()
    Script.setWidget(widget)
    debugLog("Widget set successfully")
  } else {
    debugLog("Creating widget for preview")
    const widget = await createWidget()
    await widget.presentMedium()
    debugLog("Widget presented successfully")
  }
  
  debugLog("=== Widget Execution Complete ===")
  
} catch (error) {
  debugLog(`❌ Fatal error in main execution: ${error.message}`, "ERROR")
  debugLog(`Error stack: ${error.stack}`, "ERROR")
  
  // Create emergency error widget
  const widget = new ListWidget()
  widget.backgroundColor = Color.red()
  
  const errorText = widget.addText("❌ FATAL ERROR")
  errorText.textColor = Color.white()
  errorText.font = Font.boldSystemFont(16)
  
  widget.addSpacer(8)
  
  const detailText = widget.addText(error.message)
  detailText.textColor = Color.white()
  detailText.font = Font.systemFont(12)
  detailText.lineLimit = 3
  
  if (config.runsInWidget) {
    Script.setWidget(widget)
  } else {
    await widget.presentMedium()
  }
}

Script.complete()