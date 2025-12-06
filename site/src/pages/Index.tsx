import Header from "@/components/Header";
import GameContainer from "@/components/GameContainer";
import AboutSection from "@/components/AboutSection";
import Footer from "@/components/Footer";

const Index = () => {
  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header />
      <main className="flex-1">
        <GameContainer />
        <AboutSection />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
