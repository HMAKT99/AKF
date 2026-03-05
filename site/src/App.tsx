import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import SDKUsage from './components/SDKUsage';
import FormatSupport from './components/FormatSupport';
import AboutCreator from './components/AboutCreator';
import Footer from './components/Footer';

function HomePage() {
  return (
    <>
      <Hero />
      <SDKUsage />
      <FormatSupport />
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

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-surface">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/about" element={<AboutPage />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
