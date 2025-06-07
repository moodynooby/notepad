importScripts("js/libraries/cache-polyfill.js");

let CACHE_VERSION = "app-v26";
let CACHE_FILES = [
  "/",
  "index.html",
  "js/libraries/jquery.min.js",
  "js/libraries/bootstrap.min.js",
  "js/libraries/sweetalert2.all.min.js",
  "js/libraries/jspdf.umd.min.js",
  "js/app.js",
  "js/utils.js",
  "js/selector.js",
  "css/bootstrap.min.css",
  "css/style.css",
  "img/todotxt_ico.png",
  "img/todotxt_ico-hidden.png",
  "manifest.json",
  "img/tooltip.svg",
  "fonts/OpenDyslexic-Regular.otf",
  "fonts/Cookie-Regular.ttf",
  "img/navbar/close_fullscreen_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
  "img/navbar/content_copy_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
  "img/navbar/dark-theme.svg",
  "img/navbar/delete_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
  "img/navbar/design_services_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
  "img/navbar/download_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
  "img/navbar/fullscreen_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
  "img/navbar/hourglass_top_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
  "img/navbar/keyboard_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
  "img/navbar/light-theme.svg",
  "img/navbar/mic_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
  "img/navbar/open_in_full_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
  "img/navbar/pip_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
  "img/navbar/settings_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
  "img/navbar/share_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
  "img/navbar/stop_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
  "img/navbar/view_kanban_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg",
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE_VERSION).then(function (cache) {
      console.log("Opened cache");
      return cache.addAll(CACHE_FILES);
    })
  );
});

self.addEventListener("fetch", function (event) {
  let online = navigator.onLine;
  if (!online) {
    event.respondWith(
      caches.match(event.request).then(function (res) {
        if (res) {
          return res;
        }
        requestBackend(event);
      })
    );
  }
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(
        keys.map(function (key, i) {
          if (key !== CACHE_VERSION) {
            return caches.delete(keys[i]);
          }
        })
      );
    })
  );
});

function requestBackend(event) {
  var url = event.request.clone();
  return fetch(url).then(function (res) {
    //if not a valid response send the error
    if (!res || res.status !== 200 || res.type !== "basic") {
      return res;
    }

    var response = res.clone();

    caches.open(CACHE_VERSION).then(function (cache) {
      cache.put(event.request, response);
    });

    return res;
  });
}
