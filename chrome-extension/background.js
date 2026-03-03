/**
 * Traced — background.js (service worker)
 * Handles cache coordination between tabs.
 */

// Simple in-memory cache shared across popup lookups
const brandCache = {};

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === 'CACHE_SET') {
    brandCache[msg.name] = msg.data;
  }
  if (msg.type === 'CACHE_GET') {
    sendResponse({ data: brandCache[msg.name] || null });
  }
  return true;
});

// On extension install: log ready state
chrome.runtime.onInstalled.addListener(() => {
  console.log('Traced extension installed.');
});
