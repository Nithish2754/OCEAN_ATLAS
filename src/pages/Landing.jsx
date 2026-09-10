import Navbar from '../components/Navbar';
import Hero from '../components/Hero';
import About from '../components/About';
import DepositTypes from '../components/DepositTypes';
import Technology from '../components/Technology';
import Impact from '../components/Impact';
import Footer from '../components/Footer';

export default function Landing() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <main>
        <Hero />
        <About />
        <DepositTypes />
        <Technology />
        <Impact />
      </main>
      <Footer />
    </div>
  );
}
