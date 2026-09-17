// Register Service Worker
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(registration => {
        console.log('ServiceWorker registration successful with scope: ', registration.scope);
      })
      .catch(error => {
        console.log('ServiceWorker registration failed: ', error);
      });
  });
}

// Handle PWA install prompt
let deferredPrompt;
let installBtn = null;

window.addEventListener('beforeinstallprompt', (e) => {
  // Prevent Chrome 67 and earlier from automatically showing the prompt
  e.preventDefault();
  // Stash the event so it can be triggered later
  deferredPrompt = e;
  
  // Create install button only if it doesn't exist
  if (!installBtn) {
    installBtn = document.createElement('button');
    installBtn.textContent = 'Install App';
    installBtn.style.display = 'none';
    installBtn.className = 'btn btn-primary pwa-install-btn';
    document.body.appendChild(installBtn);
    
    installBtn.addEventListener('click', (e) => {
      // Hide the app provided install promotion
      installBtn.style.display = 'none';
      // Show the install prompt
      if (deferredPrompt) {
        deferredPrompt.prompt();
        // Wait for the user to respond to the prompt
        deferredPrompt.userChoice.then((choiceResult) => {
          if (choiceResult.outcome === 'accepted') {
            console.log('User accepted the A2HS prompt');
          } else {
            console.log('User dismissed the A2HS prompt');
          }
          deferredPrompt = null;
        });
      }
    });
  }
  
  // Update UI to notify the user they can add to home screen
  installBtn.style.display = 'block';
});

// Hide install button if app is already installed
window.addEventListener('appinstalled', () => {
  if (installBtn) {
    installBtn.style.display = 'none';
  }
  console.log('PWA was installed');
});