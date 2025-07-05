import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import BackgroundVideo from "./components/BackgroundVideo.jsx";
import Landing from './Landing';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BackgroundVideo />
    <Landing />
  </React.StrictMode>,
);
