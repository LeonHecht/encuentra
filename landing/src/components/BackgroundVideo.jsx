import backgroundVideo from '../assets/8731388-hd_1920_1080_25fps.mp4';

export default function BackgroundVideo() {
  return (
    <div className="pointer-events-none absolute inset-0 z-0 overflow-hidden">
      <video
        className="h-full w-full object-cover opacity-80 grayscale"
        autoPlay
        loop
        muted
        playsInline
        aria-hidden="true"
      >
        <source src={backgroundVideo} type="video/mp4" />
      </video>
      <div className="absolute inset-0 bg-white/60" />
    </div>
  );
}
