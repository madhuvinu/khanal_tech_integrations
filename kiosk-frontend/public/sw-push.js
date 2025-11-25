/**
 * Service Worker Push Notification Handler
 * This file is imported by the main service worker to handle push events
 */

// Listen for push events
self.addEventListener('push', function(event) {
  console.log('🔔 Push event received:', event)
  
  let notificationData = {
    title: '🔔 New Notification',
    body: 'You have a new notification from Khanal Foods',
    icon: '/assets/khanal_tech_integrations/images/favicon.png',
    badge: '/assets/khanal_tech_integrations/images/favicon.png',
    data: {}
  }
  
  // Parse push data
  if (event.data) {
    console.log('📦 Push data exists, attempting to parse...')
    try {
      const rawText = event.data.text()
      console.log('📝 Raw push data text:', rawText)
      
      const data = JSON.parse(rawText)
      console.log('✅ Parsed push data:', data)
      
      notificationData = {
        title: data.title || notificationData.title,
        body: data.body || data.message || notificationData.body,
        icon: data.icon || notificationData.icon,
        badge: data.badge || notificationData.badge,
        data: data.data || data,
        tag: data.tag || 'khanal-push-' + Date.now(),
        requireInteraction: data.requireInteraction || false,
        silent: data.silent || false
      }
      console.log('📋 Final notification data:', notificationData)
    } catch (e) {
      console.error('❌ Error parsing push data:', e)
      // If data is text, use it as body
      try {
        notificationData.body = event.data.text() || notificationData.body
      } catch (e2) {
        console.error('❌ Error getting text:', e2)
      }
    }
  } else {
    console.log('⚠️ No push data in event')
  }
  
  console.log('🚀 Showing notification with title:', notificationData.title)
  
  // Show notification
  const promiseChain = self.registration.showNotification(notificationData.title, {
    body: notificationData.body,
    icon: notificationData.icon,
    badge: notificationData.badge,
    data: notificationData.data,
    tag: notificationData.tag,
    requireInteraction: notificationData.requireInteraction,
    silent: notificationData.silent,
    vibrate: [200, 100, 200]
  }).then(() => {
    console.log('✅ Notification shown successfully!')
  }).catch(err => {
    console.error('❌ Error showing notification:', err)
  })
  
  event.waitUntil(promiseChain)
})

// Listen for notification clicks
self.addEventListener('notificationclick', function(event) {
  console.log('Notification clicked:', event)
  
  event.notification.close()
  
  // Get notification data
  const notificationData = event.notification.data || {}
  
  // Determine URL to open
  let urlToOpen = '/'
  
  if (notificationData.route) {
    urlToOpen = notificationData.route
  } else if (notificationData.url) {
    urlToOpen = notificationData.url
  } else if (notificationData.type && notificationData.doc_name) {
    // Build route based on type
    switch (notificationData.type) {
      case 'production_order':
        urlToOpen = `/production-order/${notificationData.doc_name}`
        break
      case 'grn':
        urlToOpen = `/grn/${notificationData.doc_name}`
        break
      default:
        urlToOpen = '/'
    }
  }
  
  // Open or focus the window
  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then(function(clientList) {
      // Check if there's already a window open
      for (let i = 0; i < clientList.length; i++) {
        const client = clientList[i]
        if (client.url.includes(urlToOpen) && 'focus' in client) {
          return client.focus()
        }
      }
      
      // Open new window if none exists
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen)
      }
    })
  )
})

// Listen for notification close
self.addEventListener('notificationclose', function(event) {
  console.log('Notification closed:', event)
  
  // You can track notification dismissals here if needed
  const notificationData = event.notification.data || {}
  
  // Optionally send analytics or update backend
  if (notificationData.id) {
    // Track that notification was dismissed
    fetch('/api/method/khanal_tech_integrations.api.push_notifications.mark_notification_dismissed', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        notification_id: notificationData.id
      })
    }).catch(err => {
      console.error('Error tracking notification dismissal:', err)
    })
  }
})

