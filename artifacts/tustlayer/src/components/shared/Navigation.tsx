import Link from "next/link";

export function Navigation() {
  return (
    <nav className="site-nav">
      <Link href="/" className="nav-brand">
        <span className="nav-shield" aria-hidden="true" />
        TrustLayer AI
      </Link>
      <div className="nav-links">
        <Link href="/#scam-reality">The Problem</Link>
        <Link href="/#forensic-scan">How It Works</Link>
        <Link href="/product/qr" className="nav-tool-link">QR Inspector</Link>
        <Link href="/product/document" className="nav-tool-link">Doc Scanner</Link>
        <Link href="/product" className="nav-cta">
          Try Scanner
        </Link>
      </div>
    </nav>
  );
}
