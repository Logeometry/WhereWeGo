// src/setupProxy.js
const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function (app) {
  app.use(
    '/api/v1',
    createProxyMiddleware({
      target: 'https://wherewego-backend-production.up.railway.app',
      changeOrigin: true,
      secure: false,
      // logLevel: 'debug',
    })
  );
};
