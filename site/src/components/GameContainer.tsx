import { Play } from "lucide-react";

const GameContainer = () => {
  return (
    <section className="w-full px-4 md:px-8 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Game Title */}
        <div className="text-center mb-8">
          <h1 className="text-6xl md:text-8xl font-bold text-naja-title tracking-tight">
            Naja
          </h1>
          <p className="text-muted-foreground text-lg mt-2 italic">
            O clássico jogo da cobrinha
          </p>
        </div>

        {/* Game Frame */}
        <div className="game-container aspect-[4/3] w-full relative">
          {/* Grid Pattern Background */}
          <div className="absolute inset-0 grid-pattern opacity-60" />
          
          {/* Placeholder for WebAssembly game */}
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-6">
            {/* Snake and Apple Visual */}
            <div className="flex items-center gap-1 animate-float">
              <div className="w-8 h-8 rounded bg-accent" />
              <div className="w-8 h-8 rounded bg-primary" />
              <div className="w-8 h-8 rounded bg-primary opacity-80" />
              <div className="w-8 h-8 rounded bg-primary opacity-60" />
            </div>
            
            <p className="text-muted-foreground text-center px-4">
              O jogo WebAssembly será carregado aqui
            </p>
            
            <button className="btn-naja flex items-center gap-2">
              <Play className="w-5 h-5" />
              Iniciar Jogo
            </button>
          </div>
        </div>

        {/* Controls hint */}
        <div className="mt-6 flex justify-center gap-6 text-muted-foreground text-sm">
          <span>↑ ↓ ← → para mover</span>
          <span>ESC para pausar</span>
        </div>
      </div>
    </section>
  );
};

export default GameContainer;
