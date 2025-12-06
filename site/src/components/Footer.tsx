import { Github, Heart } from "lucide-react";

const Footer = () => {
  return (
    <footer className="w-full px-4 md:px-8 py-8 border-t border-border">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-muted-foreground text-sm">
          <span>Feito com</span>
          <Heart className="w-4 h-4 text-accent fill-accent" />
          <span>pelos alunos de OpenSource 2025</span>
        </div>
        
        <div className="flex items-center gap-6">
          <a
            href="https://github.com/fossguild/naja"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-muted-foreground hover:text-primary transition-colors"
          >
            <Github className="w-5 h-5" />
            <span className="text-sm">fossguild/naja</span>
          </a>
        </div>
        
        <div className="text-muted-foreground text-sm">
          © {new Date().getFullYear()} Naja Project
        </div>
      </div>
    </footer>
  );
};

export default Footer;
