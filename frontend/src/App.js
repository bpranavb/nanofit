import { useState } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./components/LandingPage";
import TryOnApp from "./components/TryOnApp";

function App() {
  return (
    // Added 'font-sans' to apply Inter and 'bg-surface-primary' for the theme
    <div className="App font-sans bg-surface-primary min-h-screen">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/app" element={<TryOnApp />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;