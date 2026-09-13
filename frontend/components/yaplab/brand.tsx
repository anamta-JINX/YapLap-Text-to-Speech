import { Asterisk } from "lucide-react";

type BrandProps = {
  footer?: boolean;
};

export function Brand({ footer = false }: BrandProps) {
  return (
    <a className={`brand${footer ? " footer-brand" : ""}`} href="#home" aria-label="YapLab home">
      <span>YapLab</span>
      <Asterisk className="brand-spark" aria-hidden="true" strokeWidth={2.5} />
    </a>
  );
}
