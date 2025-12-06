import { BookOpen, Code, Users } from "lucide-react";

const AboutSection = () => {
  const features = [
    {
      icon: BookOpen,
      title: "Educacional",
      description:
        "Desenvolvido como recurso instrucional para estudantes de Ciência da Computação do ICMC USP.",
    },
    {
      icon: Code,
      title: "Open Source",
      description:
        "Código mínimo mas funcional, projetado para que estudantes consertem bugs e implementem novas features.",
    },
    {
      icon: Users,
      title: "Colaborativo",
      description:
        "Introduz práticas de desenvolvimento Open Source e metodologias de gestão de projetos.",
    },
  ];

  return (
    <section id="sobre" className="w-full px-4 md:px-8 py-16">
      <div className="max-w-6xl mx-auto">
        {/* Section Title */}
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-foreground mb-4">
            Sobre o Projeto
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            O Naja é uma implementação do clássico jogo "Snake" dos anos 80,
            desenvolvido em Python utilizando a biblioteca Pygame.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-card rounded-xl p-6 border border-border hover:border-primary/50 transition-all duration-300 group"
            >
              <div className="w-12 h-12 rounded-lg bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                <feature.icon className="w-6 h-6 text-primary" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                {feature.title}
              </h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* ICMC Section */}
        <div className="bg-card rounded-xl p-8 border border-border flex flex-col md:flex-row items-center gap-8">
          <div className="flex-shrink-0">
            <img
              src="/logoicmc_branco.webp"
              alt="Logo ICMC USP"
              className="h-24 md:h-32 object-contain"
            />
          </div>
          <div>
            <h3 className="text-xl font-semibold text-foreground mb-3">
              ICMC - Instituto de Ciências Matemáticas e de Computação
            </h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              O Instituto de Ciências Matemáticas e de Computação (ICMC) é uma
              das principais unidades da Universidade de São Paulo (USP),
              localizado no campus de São Carlos. Reconhecido
              internacionalmente, o instituto é um centro de excelência em
              ensino e pesquisa nas áreas de Matemática, Computação e
              Estatística, sendo responsável pela formação de alguns dos
              melhores profissionais e pesquisadores da América Latina. Para
              saber mais sobre a disciplina de Desenvolvimento de Software
              Livre, que incentiva projetos como este,{' '}
              <a
                href="https://uspdigital.usp.br/jupiterweb/listarGradeCurricular?codcg=55&codcur=55041&codhab=0&tipo=N"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary underline"
              >
                clique aqui
              </a>
              .
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default AboutSection;
