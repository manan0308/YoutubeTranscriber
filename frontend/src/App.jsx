import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './components/theme-provider';
import { Toaster } from 'sonner';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import TranscriptPage from './pages/TranscriptPage';
import NotFoundPage from './pages/NotFoundPage';

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="youtube-transcriber-theme">
      <Toaster position="top-right" />
      <Router>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="/transcript/:videoId" element={<TranscriptPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
