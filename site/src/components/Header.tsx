import { Github } from "lucide-react";

const Header = () => {
  const scrollToAbout = () => {
    document.getElementById("sobre")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <header className="w-full py-6 px-4 md:px-8 border-b border-border">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg overflow-hidden bg-primary flex items-center justify-center animate-glow">
            <img
              src="/naja-logo.png"
              alt="Ícone do projeto Naja"
              className="w-full h-full object-cover"
            />
          </div>
          <span className="text-2xl font-bold text-naja-title">Naja</span>
        </div>
        
        {/* Navigation */}
        <nav className="flex items-center gap-6">
          <button
            onClick={scrollToAbout}
            className="text-muted-foreground hover:text-foreground transition-colors font-medium"
          >
            Sobre o Projeto
          </button>
          
          <a
            href="https://github.com/fossguild/naja"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-github flex items-center gap-2"
          >
            <Github className="w-5 h-5" />
            <span className="hidden sm:inline">Ver no GitHub</span>
          </a>
        </nav>
      </div>
    </header>
  );
};

export default Header;
