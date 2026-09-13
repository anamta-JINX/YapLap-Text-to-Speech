import { Brand } from "./brand";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <Brand footer />
      <p>Your words called. They wanna yap.</p>
      <div className="footer-credit">
        <strong>Created by Anamta Gohar</strong>
        <span>YAPLAB © 2026 · v2.3</span>
      </div>
    </footer>
  );
}
