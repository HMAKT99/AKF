import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import ValueProps from './components/ValueProps';
import SDKUsage from './components/SDKUsage';
import FormatSupport from './components/FormatSupport';
import FormatComparison from './components/FormatComparison';
import SecurityIntegration from './components/SecurityIntegration';
import AgentIntegration from './components/AgentIntegration';
import WorksWith from './components/WorksWith';
import DownloadSection from './components/DownloadSection';
import AboutCreator from './components/AboutCreator';
import PersonasPage from './components/PersonasPage';
import Footer from './components/Footer';

function HomePage() {
  return (
    <>
      <Hero />
      <ValueProps />
      <SDKUsage />
      <FormatSupport />
      <FormatComparison />
      <AgentIntegration />
      <SecurityIntegration />
      <WorksWith />
      <DownloadSection />
    </>
  );
}

function AboutPage() {
  return (
    <div className="pt-14">
      <AboutCreator />
    </div>
  );
}

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <div className="min-h-screen bg-surface">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/personas" element={<PersonasPage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
