import { useEffect } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Problem from './components/Problem';
import FormatGlance from './components/FormatGlance';
import BenefitsTable from './components/BenefitsTable';
import SDKUsage from './components/SDKUsage';
import FormatSupport from './components/FormatSupport';
import Footer from './components/Footer';

function useScrollReveal() {
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -40px 0px' }
    );

    document.querySelectorAll('.section-animate').forEach((el) => {
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);
}

export default function App() {
  useScrollReveal();

  return (
    <div className="min-h-screen bg-surface">
      <Navbar />
      <main>
        <div className="animate-fade-up">
          <Hero />
        </div>
        <div className="section-animate">
          <Problem />
        </div>
        <div className="section-animate">
          <FormatGlance />
        </div>
        <div className="section-animate">
          <BenefitsTable />
        </div>
        <div className="section-animate">
          <SDKUsage />
        </div>
        <div className="section-animate">
          <FormatSupport />
        </div>
      </main>
      <Footer />
    </div>
  );
}
