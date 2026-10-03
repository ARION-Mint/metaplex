import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import { useWallet } from '@solana/wallet-adapter-react';
import { shortenAddress, useStore, useWalletModal } from '@oyster/common';
import { useTypewriter } from '../../hooks/useTypewriter';

// Optional background clip. Set NEXT_PUBLIC_HERO_VIDEO_URL to your own video;
// without one the animated brand backdrop is scrubbed by the mouse instead.
const VIDEO_URL = process.env.NEXT_PUBLIC_HERO_VIDEO_URL;
const SENSITIVITY = 0.8;

const NAV_LINKS = [
  { label: 'Explore', to: '/' },
  { label: 'Collections', to: '/collections' },
  { label: 'Artwork', to: '/artworks' },
  { label: 'Creators', to: '/artists' },
];

const ACTIONS = [
  { label: 'Explore live drops', to: '/' },
  { label: 'Mint your first NFT', to: '/art/create/0' },
  { label: 'Browse collections', to: '/collections' },
  { label: 'Meet the creators', to: '/artists' },
];

const GREETING =
  'Glad you stopped in. Rare art tends to find its collectors. Now, what are we minting today?';

const CopyIcon = () => (
  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden>
    <rect x="3.5" y="3.5" width="8" height="8" rx="1.5" stroke="currentColor" />
    <path
      d="M8.5 2V1.5A1 1 0 0 0 7.5.5h-6a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1H2"
      stroke="currentColor"
    />
  </svg>
);

const useMouseScrub = (
  videoRef: React.RefObject<HTMLVideoElement>,
  rootRef: React.RefObject<HTMLDivElement>,
) => {
  useEffect(() => {
    let prevX: number | null = null;
    let targetTime = 0;
    let seeking = false;
    // Drives the brand backdrop when there is no video (0..1).
    let backdrop = 0.5;

    const seek = (video: HTMLVideoElement) => {
      if (Math.abs(video.currentTime - targetTime) < 0.001) return;
      seeking = true;
      video.currentTime = targetTime;
    };

    const onSeeked = () => {
      seeking = false;
      const video = videoRef.current;
      if (video) seek(video);
    };

    const onMouseMove = (e: MouseEvent) => {
      if (prevX === null) {
        prevX = e.clientX;
        return;
      }
      const delta = e.clientX - prevX;
      prevX = e.clientX;
      const ratio = (delta / window.innerWidth) * SENSITIVITY;

      backdrop = Math.min(1, Math.max(0, backdrop + ratio));
      rootRef.current?.style.setProperty('--scrub', String(backdrop));

      const video = videoRef.current;
      if (!video || !video.duration || isNaN(video.duration)) return;
      targetTime = Math.min(
        video.duration,
        Math.max(0, targetTime + ratio * video.duration),
      );
      if (!seeking) seek(video);
    };

    const video = videoRef.current;
    video?.addEventListener('seeked', onSeeked);
    window.addEventListener('mousemove', onMouseMove);
    return () => {
      video?.removeEventListener('seeked', onSeeked);
      window.removeEventListener('mousemove', onMouseMove);
    };
  }, [videoRef, rootRef]);
};

export const LandingView = () => {
  const rootRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [videoFailed, setVideoFailed] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [showActions, setShowActions] = useState(false);
  const [copied, setCopied] = useState(false);
  const { displayed, done } = useTypewriter(GREETING);
  useMouseScrub(videoRef, rootRef);

  const { storeAddress } = useStore();
  const { wallet, connect, connected, publicKey } = useWallet();
  const { setVisible } = useWalletModal();

  useEffect(() => {
    const timer = setTimeout(() => setShowActions(true), 400);
    return () => clearTimeout(timer);
  }, []);

  const onConnect = useCallback(() => {
    setMenuOpen(false);
    if (connected) return;
    if (wallet) connect().catch(() => {});
    else setVisible(true);
  }, [connected, wallet, connect, setVisible]);

  const shareValue = storeAddress || window.location.origin;
  const onCopy = useCallback(() => {
    navigator.clipboard.writeText(shareValue).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }, [shareValue]);

  const walletLabel =
    connected && publicKey
      ? shortenAddress(publicKey.toBase58())
      : 'Connect wallet';

  const navLinks = NAV_LINKS.map((link, i) => (
    <React.Fragment key={link.label}>
      <Link to={link.to} onClick={() => setMenuOpen(false)}>
        {link.label}
      </Link>
      {i < NAV_LINKS.length - 1 && <span className="mx-hero-comma">, </span>}
    </React.Fragment>
  ));

  return (
    <div className="mx-hero" ref={rootRef}>
      <div className="mx-hero-backdrop" aria-hidden>
        <span className="mx-hero-glow mx-hero-glow--mint" />
        <span className="mx-hero-glow mx-hero-glow--violet" />
        <span className="mx-hero-grid" />
      </div>
      {VIDEO_URL && !videoFailed && (
        <video
          ref={videoRef}
          className="mx-hero-video"
          src={VIDEO_URL}
          muted
          playsInline
          preload="auto"
          onError={() => setVideoFailed(true)}
        />
      )}
      <div className="mx-hero-shade" aria-hidden />

      <nav className="mx-hero-nav">
        <Link to="/" className="mx-hero-logo">
          <img src="/metaplex-logo.svg" alt="Metaplex" />
          <span className="mx-hero-asterisk">✳︎</span>
        </Link>
        <div className="mx-hero-links">{navLinks}</div>
        <button type="button" className="mx-hero-cta" onClick={onConnect}>
          {walletLabel}
        </button>
        <button
          type="button"
          className={`mx-hero-burger${menuOpen ? ' is-open' : ''}`}
          aria-label="Toggle menu"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen(open => !open)}
        >
          <span />
          <span />
          <span />
        </button>
      </nav>

      <div className={`mx-hero-overlay${menuOpen ? ' is-open' : ''}`}>
        {NAV_LINKS.map(link => (
          <Link key={link.label} to={link.to} onClick={() => setMenuOpen(false)}>
            {link.label}
          </Link>
        ))}
        <button type="button" className="mx-hero-cta" onClick={onConnect}>
          {walletLabel}
        </button>
      </div>

      <section className="mx-hero-section">
        <div className="mx-hero-content">
          <p className="mx-hero-intro">
            Hey there, meet M.I.N.T.,
            <br />
            your Marketplace Intelligent NFT Tour-guide
          </p>

          <p className="mx-hero-typed">
            {displayed}
            {!done && <span className="mx-hero-cursor" />}
          </p>

          <div className={`mx-hero-actions${showActions ? ' is-visible' : ''}`}>
            {ACTIONS.map(action => (
              <Link key={action.label} to={action.to} className="mx-hero-pill">
                {action.label}
              </Link>
            ))}
            <button
              type="button"
              className="mx-hero-pill mx-hero-pill--outline"
              onClick={onCopy}
              title={shareValue}
            >
              <span>
                {copied ? (
                  'Copied!'
                ) : storeAddress ? (
                  <>
                    Store: <u>{shortenAddress(storeAddress)}</u>
                  </>
                ) : (
                  <>
                    Share: <u>{window.location.host}</u>
                  </>
                )}
              </span>
              <CopyIcon />
            </button>
          </div>
        </div>
      </section>
    </div>
  );
};
