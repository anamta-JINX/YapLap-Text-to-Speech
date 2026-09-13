import { ArrowRight, Menu } from "lucide-react";

import { Brand } from "./brand";

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="topbar">
        <Brand />

        <nav aria-label="Main navigation">
          <a className="active" href="#home">Home</a>
          <a href="#features">Features</a>
          <a href="#voices">Voices</a>
          <a href="#about">About</a>
        </nav>

        <div className="topbar-actions">
          <button className="header-button sign-in" type="button" title="Accounts are coming soon" disabled>
            Sign In
          </button>
          <a className="header-button get-started" href="#studio">
            Get Started <ArrowRight aria-hidden="true" size={18} />
          </a>
          <a className="mobile-menu" href="#studio" aria-label="Open the YapLab studio">
            <Menu aria-hidden="true" size={22} />
          </a>
        </div>
      </div>
    </header>
  );
}
