import React from 'react';
import { useNavigate } from 'react-router-dom';
import BeforeAfterSlider from './BeforeAfterSlider';
import '../styles/LandingPage.css';

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="landing-page min-h-screen bg-[#020617] text-white selection:bg-violet-500/30">
      {/* Hero Section - Two Column Grid */}
      <div className="hero-section relative max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-2 gap-12 items-center min-h-[90vh]">
        
        {/* Decorative Background Orbs */}
        <div className="absolute top-[10%] left-[-5%] w-[30%] h-[30%] bg-violet-600/10 blur-[120px] rounded-full" />

        {/* Left Column: Text Content */}
        <div className="hero-content relative z-10 text-left">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-white/10 bg-white/5 backdrop-blur-md text-sm font-medium text-violet-300 mb-8">
            <span className="flex h-2 w-2 rounded-full bg-violet-500" />
            Virtual Try-On Made Simple
          </div>

          <h1 className="hero-title text-6xl md:text-7xl font-extrabold tracking-tighter leading-[1.1] mb-6">
            NANOFIT <br /> 
            <span className="text-white/60">Virtual Try-On</span>
          </h1>
          
          <p className="hero-subtitle text-lg text-slate-400 max-w-xl mb-10 leading-relaxed">
            See yourself in any outfit instantly with AI-powered technology. 
            Upload your photo and the clothes you want to try — we'll do the rest!
          </p>

          <div className="flex flex-wrap gap-4">
            <button 
              onClick={() => navigate('/app')}
              className="px-10 py-4 bg-white text-black rounded-full font-bold hover:bg-slate-200 transition-all"
            >
              Start Trying On ↗
            </button>
            <button className="px-10 py-4 bg-white/5 border border-white/10 rounded-full font-bold backdrop-blur-md hover:bg-white/10 transition-all">
              How it works
            </button>
          </div>
        </div>

        {/* Right Column: Before & After Slider */}
        <div className="hero-image relative z-10 flex justify-center lg:justify-end">
          <div className="absolute inset-0 bg-violet-600/10 blur-[100px] rounded-full opacity-50" />
          <div className="demo-slider-container w-full max-w-[500px] aspect-[4/5] rounded-[2rem] overflow-hidden border border-white/10 bg-black/40 backdrop-blur-sm shadow-2xl">
            <BeforeAfterSlider
              beforeImage="https://customer-assets.emergentagent.com/job_tablet-bugfix/artifacts/z4o9uu7w_Gemini_Generated_Image_oh7qwjoh7qwjoh7q%20%281%29.png"
              afterImage="https://customer-assets.emergentagent.com/job_tablet-bugfix/artifacts/brlblti7_Gemini_Generated_Image_oh7qwjoh7qwjoh7q.png"
              alt="Virtual Try-On Demo"
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-12 text-center border-t border-white/5">
        <p className="text-slate-600 text-xs tracking-widest uppercase">© 2025 NANOFIT. POWERED BY AI.</p>
      </footer>
    </div>
  );
};

export default LandingPage;