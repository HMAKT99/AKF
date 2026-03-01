import { useState, useEffect, useCallback } from "react";

/** Simulate typing text character by character */
export function useTypingEffect(
  text: string,
  active: boolean,
  speed: number = 12
): { displayed: string; done: boolean } {
  const [index, setIndex] = useState(0);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!active) { setIndex(0); setDone(false); return; }
    if (index >= text.length) { setDone(true); return; }
    const timer = setTimeout(() => setIndex((i) => i + 1), speed);
    return () => clearTimeout(timer);
  }, [active, index, text, speed]);

  return { displayed: active ? text.slice(0, index) : "", done };
}

/** Trigger a delayed action */
export function useDelayedAction(delayMs: number) {
  const [triggered, setTriggered] = useState(false);
  const [complete, setComplete] = useState(false);

  useEffect(() => {
    if (!triggered) return;
    const timer = setTimeout(() => setComplete(true), delayMs);
    return () => clearTimeout(timer);
  }, [triggered, delayMs]);

  const trigger = useCallback(() => setTriggered(true), []);
  const reset = useCallback(() => { setTriggered(false); setComplete(false); }, []);

  return { trigger, active: triggered && !complete, complete, reset };
}

/** Animate pipeline stages in sequence */
export function usePipelineAnimation(
  stageCount: number,
  stageDelayMs: number,
  active: boolean
) {
  const [activeStage, setActiveStage] = useState(-1);

  useEffect(() => {
    if (!active) { setActiveStage(-1); return; }
    if (activeStage >= stageCount - 1) return;
    const timer = setTimeout(
      () => setActiveStage((s) => s + 1),
      activeStage < 0 ? 300 : stageDelayMs
    );
    return () => clearTimeout(timer);
  }, [active, activeStage, stageCount, stageDelayMs]);

  return {
    activeStage,
    allComplete: activeStage >= stageCount - 1,
    stageActive: (i: number) => i <= activeStage,
  };
}
