"use client";

import { useEffect, useRef } from "react";

const TRAIL_LENGTH = 7;

export function PlaneCursor() {
  const layerRef = useRef<HTMLDivElement>(null);
  const planeRef = useRef<HTMLDivElement>(null);
  const trailRefs = useRef<Array<HTMLSpanElement | null>>([]);

  useEffect(() => {
    const finePointer = window.matchMedia("(pointer: fine)");
    if (!finePointer.matches) return;

    const layer = layerRef.current;
    const plane = planeRef.current;
    if (!layer || !plane) return;

    const pointer = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
    const trail = Array.from({ length: TRAIL_LENGTH }, () => ({ ...pointer }));
    let frame = 0;

    const draw = () => {
      // Keep the pixel artwork on whole pixels, with its tip at the click point.
      plane.style.transform = `translate3d(${Math.round(pointer.x) - 2}px, ${Math.round(pointer.y) - 1}px, 0)`;

      let lead = pointer;
      trail.forEach((point, index) => {
        const ease = index === 0 ? 0.28 : 0.42;
        point.x += (lead.x - point.x) * ease;
        point.y += (lead.y - point.y) * ease;
        const dot = trailRefs.current[index];
        if (dot) {
          dot.style.transform = `translate3d(${point.x - 3}px, ${point.y - 3}px, 0)`;
        }
        lead = point;
      });

      frame = window.requestAnimationFrame(draw);
    };

    const onPointerMove = (event: PointerEvent) => {
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      document.documentElement.classList.add("has-plane-cursor");
      layer.classList.add("is-active");
    };
    const onPointerDown = () => layer.classList.add("is-clicking");
    const onPointerUp = () => layer.classList.remove("is-clicking");
    const onPointerLeave = () => {
      layer.classList.remove("is-active", "is-clicking");
      document.documentElement.classList.remove("has-plane-cursor");
    };

    window.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("pointerdown", onPointerDown, { passive: true });
    window.addEventListener("pointerup", onPointerUp, { passive: true });
    document.documentElement.addEventListener("mouseleave", onPointerLeave);
    frame = window.requestAnimationFrame(draw);

    return () => {
      document.documentElement.classList.remove("has-plane-cursor");
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("pointerup", onPointerUp);
      document.documentElement.removeEventListener("mouseleave", onPointerLeave);
      window.cancelAnimationFrame(frame);
    };
  }, []);

  return (
    <div ref={layerRef} className="plane-cursor-layer" aria-hidden="true">
      {Array.from({ length: TRAIL_LENGTH }, (_, index) => (
        <span
          key={index}
          ref={(element) => {
            trailRefs.current[index] = element;
          }}
          className="plane-cursor-dot"
        />
      ))}
      <div ref={planeRef} className="plane-cursor-icon">
        <span className="plane-cursor-sprite" />
      </div>
    </div>
  );
}
