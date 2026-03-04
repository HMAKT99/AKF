import Navbar from './components/Navbar';
import Hero from './components/Hero';
import SDKUsage from './components/SDKUsage';
import FormatSupport from './components/FormatSupport';
import AboutCreator from './components/AboutCreator';
import Footer from './components/Footer';

export default function App() {
  return (
    <div className="min-h-screen bg-surface">
      <Navbar />
      <main>
        <Hero />
        <SDKUsage />
        <FormatSupport />
        <AboutCreator />
      </main>
      <Footer />
    </div>
  );
}
