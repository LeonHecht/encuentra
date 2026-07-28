import { useEffect, useRef, useState } from 'react';

export function HeroParallax({ children, className = '' }) {
  const elementRef = useRef(null);

  useEffect(() => {
    const element = elementRef.current;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

    if (!element || reduceMotion.matches) return undefined;

    let frameId;

    const updatePosition = () => {
      frameId = undefined;
      const progress = Math.min(window.scrollY / window.innerHeight, 1);

      element.style.setProperty('--hero-shift', `${progress * -110}px`);
      element.style.setProperty('--hero-opacity', `${1 - progress * 0.72}`);
      element.style.setProperty('--hero-scale', `${1 - progress * 0.035}`);
    };

    const handleScroll = () => {
      if (!frameId) frameId = window.requestAnimationFrame(updatePosition);
    };

    updatePosition();
    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (frameId) window.cancelAnimationFrame(frameId);
    };
  }, []);

  return (
    <div
      ref={elementRef}
      className={`hero-parallax ${className}`}
    >
      {children}
    </div>
  );
}

export function ScrollReveal({
  children,
  className = '',
  direction = 'up',
  delay = 0,
}) {
  const elementRef = useRef(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return undefined;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(entry.isIntersecting);
      },
      {
        threshold: 0.16,
        rootMargin: '0px 0px -8% 0px',
      },
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={elementRef}
      className={`scroll-reveal scroll-reveal--${direction} ${
        isVisible ? 'is-visible' : ''
      } ${className}`}
      style={{ '--reveal-delay': `${delay}ms` }}
    >
      {children}
    </div>
  );
}
