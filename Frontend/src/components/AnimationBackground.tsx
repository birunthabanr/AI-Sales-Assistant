import { useEffect, useState } from "react";

interface Particle {
  id: number;
  left: number;
  size: number;
  duration: number;
  delay: number;
  color: string;
}

const AnimatedBackground = () => {
  const [bubbles, setBubbles] = useState<Particle[]>([]);
  const [dust, setDust] = useState<Particle[]>([]);

  useEffect(() => {
    // Generate bubbles
    const generateBubbles = () => {
      const newBubbles: Particle[] = [];
      for (let i = 0; i < 20; i++) {
        newBubbles.push({
          id: i,
          left: Math.random() * 100,
          size: Math.random() * 40 + 15,
          duration: Math.random() * 12 + 8,
          delay: Math.random() * 6,
          // shifted toward aqua–teal range
          color: `hsla(${180 + Math.random() * 60}, 70%, 65%, ${
            Math.random() * 0.3 + 0.1
          })`,
        });
      }
      setBubbles(newBubbles);
    };

    // Generate dust particles
    const generateDust = () => {
      const newDust: Particle[] = [];
      for (let i = 0; i < 35; i++) {
        newDust.push({
          id: i,
          left: Math.random() * 100,
          size: Math.random() * 10 + 2,
          duration: Math.random() * 18 + 10,
          delay: Math.random() * 8,
          // shifted toward magenta/pink range
          color: `hsla(${300 + Math.random() * 60}, 60%, 70%, ${
            Math.random() * 0.4 + 0.1
          })`,
        });
      }
      setDust(newDust);
    };

    generateBubbles();
    generateDust();

    // Regenerate particles periodically
    const bubbleInterval = setInterval(generateBubbles, 12000);
    const dustInterval = setInterval(generateDust, 15000);

    return () => {
      clearInterval(bubbleInterval);
      clearInterval(dustInterval);
    };
  }, []);

  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none">
      {/* Floating Bubbles */}
      {bubbles.map((bubble) => (
        <div
          key={`bubble-${bubble.id}`}
          className="bubble absolute rounded-full"
          style={{
            left: `${bubble.left}%`,
            width: `${bubble.size}px`,
            height: `${bubble.size}px`,
            background: `radial-gradient(circle at 30% 30%, ${bubble.color.replace(
              "0.1",
              "0.4"
            )}, ${bubble.color})`,
            border: `1px solid ${bubble.color.replace("0.1", "0.2")}`,
            animation: `bubble-rise ${bubble.duration}s linear infinite`,
            animationDelay: `${bubble.delay}s`,
            boxShadow: `0 0 20px ${bubble.color.replace("0.1", "0.3")}`,
          }}
        />
      ))}

      {/* Dust Particles */}
      {dust.map((particle) => (
        <div
          key={`dust-${particle.id}`}
          className="dust absolute rounded-full"
          style={{
            left: `${particle.left}%`,
            width: `${particle.size}px`,
            height: `${particle.size}px`,
            background: `radial-gradient(circle, ${particle.color}, transparent)`,
            animation: `dust-float ${particle.duration}s linear infinite`,
            animationDelay: `${particle.delay}s`,
            filter: "blur(0.5px)",
          }}
        />
      ))}

      {/* Extra floating highlights */}
      <div className="absolute inset-0">
        {Array.from({ length: 8 }).map((_, i) => (
          <div
            key={`float-${i}`}
            className="absolute w-3 h-3 rounded-full"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              background: `hsla(${200 + Math.random() * 80}, 60%, 70%, 0.2)`,
              animation: `float ${4 + Math.random() * 4}s ease-in-out infinite`,
              animationDelay: `${Math.random() * 2}s`,
              filter: "blur(1px)",
            }}
          />
        ))}
      </div>
    </div>
  );
};

export default AnimatedBackground;
