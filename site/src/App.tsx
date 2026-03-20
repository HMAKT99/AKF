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
import InteractiveDemo from './components/InteractiveDemo';
import AutoStamping from './components/AutoStamping';
import AmbientTrust from './components/AmbientTrust';
import SectionDivider from './ui/SectionDivider';
import AboutCreator from './components/AboutCreator';
import PersonasPage from './components/PersonasPage';
import ComparePage from './components/ComparePage';
import GetStartedPage from './components/GetStartedPage';
import ConvertPage from './components/ConvertPage';
import ValidatePage from './components/ValidatePage';
import CertifyPage from './components/CertifyPage';
import CompareC2paPage from './components/CompareC2paPage';
import ComparePurviewPage from './components/ComparePurviewPage';
import CompareWatermarkingPage from './components/CompareWatermarkingPage';
import EnterpriseReportPage from './components/EnterpriseReportPage';
import ComplianceCountdown from './components/ComplianceCountdown';
import ComplianceBanner, { useBannerVisible } from './components/ComplianceBanner';
import Footer from './components/Footer';

function HomePage() {
  return (
    <>
      {/* ── INTRO ── */}
      <Hero />
      <InteractiveDemo />
      <ValueProps />
      <AutoStamping />
      <WorksWith />

      {/* ── GET STARTED ── */}
      <div className="bg-surface-raised/50">
        <SectionDivider label="Get Started" id="get-started" />
        <SDKUsage />
        <DownloadSection />
      </div>

      {/* ── WHY AKF ── */}
      <SectionDivider label="Why AKF" id="why-akf" />
      <FormatSupport />
      <FormatComparison />
      <AgentIntegration />
      <AmbientTrust />
      <ComplianceCountdown />

      {/* ── ENTERPRISE ── */}
      <div className="bg-surface-raised/50">
        <SectionDivider label="Security" id="enterprise" />
        <SecurityIntegration />
      </div>
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

function AppShell() {
  const banner = useBannerVisible();

  return (
    <>
      <ScrollToTop />
      <div className="min-h-screen bg-surface">
        {banner.visible && (
          <ComplianceBanner onDismiss={banner.dismiss} />
        )}
        <Navbar topOffset={banner.height} />
        <main style={{ paddingTop: banner.height }}>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/personas" element={<PersonasPage />} />
            <Route path="/akf-vs-md" element={<ComparePage />} />
            <Route path="/why-akf" element={<ComparePage />} />
            <Route path="/compare" element={<ComparePage />} />
            <Route path="/get-started" element={<GetStartedPage />} />
            <Route path="/convert-to-akf" element={<ConvertPage />} />
            <Route path="/validate" element={<ValidatePage />} />
            <Route path="/certify" element={<CertifyPage />} />
            <Route path="/audit" element={<ValidatePage />} />
            <Route path="/enterprise-report" element={<EnterpriseReportPage />} />
            <Route path="/compare/c2pa" element={<CompareC2paPage />} />
            <Route path="/compare/purview" element={<ComparePurviewPage />} />
            <Route path="/compare/watermarking" element={<CompareWatermarkingPage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}
