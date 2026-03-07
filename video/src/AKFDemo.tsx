import {
  AbsoluteFill,
  Sequence,
  interpolate,
  useCurrentFrame,
  Easing,
} from "remotion";

/*
 * AKF — 60-Second Marketing Video
 * Style: Apple keynote — large type, deliberate pacing, precise motion
 *
 * Script:
 *   0-5s   "Your AI writes the report. But who trusts it?"
 *   5-12s  "No provenance. No confidence. No audit trail." → "Until now."
 *  12-20s  .akf reveal + tagline
 *  20-32s  Three capabilities (trust / provenance / compliance)
 *  32-42s  The numbers (15 tokens / 0.1s / 20+ formats)
 *  42-50s  Install simplicity
 *  50-60s  CTA — "The file format for the AI era."
 */

// ── Timing (30 fps) ──────────────────────────────
const FPS = 30;
const f = (seconds: number) => Math.round(seconds * FPS);

// ── Easing ───────────────────────────────────────
const EASE_OUT = Easing.bezier(0.16, 1, 0.3, 1); // Apple-style deceleration
const EASE_IN = Easing.bezier(0.55, 0, 1, 0.45);

function appear(
  frame: number,
  start: number,
  duration = 18,
): { opacity: number; y: number } {
  const opacity = interpolate(frame, [start, start + duration], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const y = interpolate(frame, [start, start + duration], [50, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  return { opacity, y };
}

function fadeOut(
  frame: number,
  start: number,
  duration = 12,
): number {
  return interpolate(frame, [start, start + duration], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_IN,
  });
}

// ── Colors ───────────────────────────────────────
const C = {
  bg: "#000000",
  white: "#ffffff",
  gray: "#86868b",     // Apple gray
  accent: "#2997ff",   // Apple blue
  green: "#30d158",
  amber: "#ffd60a",
};

// ── Text component (Apple-style large type) ──────
const Title: React.FC<{
  children: React.ReactNode;
  size?: number;
  color?: string;
  weight?: number;
  tracking?: string;
  style?: React.CSSProperties;
}> = ({
  children,
  size = 72,
  color = C.white,
  weight = 700,
  tracking = "-0.04em",
  style,
}) => (
  <div
    style={{
      fontSize: size,
      fontWeight: weight,
      color,
      letterSpacing: tracking,
      lineHeight: 1.1,
      fontFamily:
        "'SF Pro Display', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      textAlign: "center",
      ...style,
    }}
  >
    {children}
  </div>
);

/* ═══════════════════════════════════════════════════
   SCENE 1 — THE HOOK (0-5s)
   "Your AI writes the report."
   "But who trusts it?"
   ═══════════════════════════════════════════════════ */
const SceneHook: React.FC = () => {
  const frame = useCurrentFrame();

  const line1 = appear(frame, f(0.3));
  const line2 = appear(frame, f(1.8));
  const sceneOut = fadeOut(frame, f(4.2));

  return (
    <AbsoluteFill
      style={{ background: C.bg, opacity: sceneOut }}
      className="flex flex-col items-center justify-center gap-6"
    >
      <div style={{ opacity: line1.opacity, transform: `translateY(${line1.y}px)` }}>
        <Title size={64} weight={500} color={C.gray}>
          Your AI writes the report.
        </Title>
      </div>
      <div style={{ opacity: line2.opacity, transform: `translateY(${line2.y}px)` }}>
        <Title size={80}>
          But who{" "}
          <span style={{ color: C.accent }}>trusts</span>{" "}
          it?
        </Title>
      </div>
    </AbsoluteFill>
  );
};

/* ═══════════════════════════════════════════════════
   SCENE 2 — THE PROBLEM (5-12s)
   "No provenance. No confidence. No audit trail."
   "Until now."
   ═══════════════════════════════════════════════════ */
const SceneProblem: React.FC = () => {
  const frame = useCurrentFrame();

  const words = [
    { text: "No provenance.", start: f(0.4) },
    { text: "No confidence score.", start: f(1.2) },
    { text: "No audit trail.", start: f(2.0) },
  ];

  const untilNow = appear(frame, f(3.5), 20);
  const sceneOut = fadeOut(frame, f(6.2));

  return (
    <AbsoluteFill
      style={{ background: C.bg, opacity: sceneOut }}
      className="flex flex-col items-center justify-center"
    >
      <div className="flex flex-col items-center gap-4">
        {words.map((w) => {
          const a = appear(frame, w.start, 14);
          return (
            <div
              key={w.text}
              style={{
                opacity: a.opacity,
                transform: `translateY(${a.y}px)`,
              }}
            >
              <Title size={56} weight={500} color={C.gray}>
                {w.text}
              </Title>
            </div>
          );
        })}
      </div>

      <div
        style={{
          opacity: untilNow.opacity,
          transform: `translateY(${untilNow.y}px)`,
          marginTop: 60,
        }}
      >
        <Title size={88}>Until now.</Title>
      </div>
    </AbsoluteFill>
  );
};

/* ═══════════════════════════════════════════════════
   SCENE 3 — THE REVEAL (12-20s)
   .akf + tagline
   ═══════════════════════════════════════════════════ */
const SceneReveal: React.FC = () => {
  const frame = useCurrentFrame();

  // Logo: scale up from 0.8, with a subtle glow
  const logoOpacity = interpolate(frame, [f(0.3), f(1.2)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const logoScale = interpolate(frame, [f(0.3), f(1.2)], [0.85, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  // Horizontal rule expanding
  const ruleWidth = interpolate(frame, [f(1.5), f(2.5)], [0, 200], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  const tagline = appear(frame, f(2.5), 20);
  const subtitle = appear(frame, f(3.8), 18);
  const sceneOut = fadeOut(frame, f(7.2));

  return (
    <AbsoluteFill
      style={{ background: C.bg, opacity: sceneOut }}
      className="flex flex-col items-center justify-center"
    >
      {/* Logo */}
      <div
        style={{
          opacity: logoOpacity,
          transform: `scale(${logoScale})`,
        }}
      >
        <span
          style={{
            fontSize: 140,
            fontWeight: 800,
            color: C.accent,
            fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
            letterSpacing: "-0.03em",
          }}
        >
          .akf
        </span>
      </div>

      {/* Divider line */}
      <div
        style={{
          width: ruleWidth,
          height: 1,
          background: `linear-gradient(90deg, transparent, ${C.accent}, transparent)`,
          marginTop: 32,
          marginBottom: 32,
        }}
      />

      {/* Tagline */}
      <div style={{ opacity: tagline.opacity, transform: `translateY(${tagline.y}px)` }}>
        <Title size={48} weight={600}>
          Trust metadata for AI content
        </Title>
      </div>

      {/* Subtitle */}
      <div
        style={{
          opacity: subtitle.opacity,
          transform: `translateY(${subtitle.y}px)`,
          marginTop: 16,
        }}
      >
        <Title size={22} weight={500} color={C.gray} tracking="0.2em">
          EXIF FOR AI
        </Title>
      </div>
    </AbsoluteFill>
  );
};

/* ═══════════════════════════════════════════════════
   SCENE 4 — THREE CAPABILITIES (20-32s)
   Sequential reveals, one at a time, centered
   ═══════════════════════════════════════════════════ */
const CapabilityBeat: React.FC<{
  number: string;
  title: string;
  description: string;
  color: string;
  inStart: number;
  outStart: number;
}> = ({ number, title, description, color, inStart, outStart }) => {
  const frame = useCurrentFrame();

  const numA = appear(frame, inStart, 14);
  const titleA = appear(frame, inStart + 6, 16);
  const descA = appear(frame, inStart + 14, 16);
  const out = fadeOut(frame, outStart, 10);

  const combinedOpacity = Math.min(
    Math.min(numA.opacity, 1),
    out,
  );

  return (
    <AbsoluteFill
      style={{ background: C.bg, opacity: combinedOpacity }}
      className="flex flex-col items-center justify-center"
    >
      {/* Number */}
      <div
        style={{
          opacity: numA.opacity,
          transform: `translateY(${numA.y * 0.5}px)`,
        }}
      >
        <Title size={28} weight={500} color={color} tracking="0.15em">
          {number}
        </Title>
      </div>

      {/* Title */}
      <div
        style={{
          opacity: titleA.opacity,
          transform: `translateY(${titleA.y}px)`,
          marginTop: 16,
        }}
      >
        <Title size={88} weight={700}>
          {title}
        </Title>
      </div>

      {/* Description */}
      <div
        style={{
          opacity: descA.opacity,
          transform: `translateY(${descA.y}px)`,
          marginTop: 20,
        }}
      >
        <Title size={28} weight={400} color={C.gray} tracking="-0.01em">
          {description}
        </Title>
      </div>
    </AbsoluteFill>
  );
};

const SceneCapabilities: React.FC = () => {
  const frame = useCurrentFrame();

  // Three beats, ~4s each
  const beat1Visible = frame < f(4.2);
  const beat2Visible = frame >= f(3.8) && frame < f(8.2);
  const beat3Visible = frame >= f(7.8);

  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {beat1Visible && (
        <Sequence from={0} durationInFrames={f(4.5)}>
          <CapabilityBeat
            number="01"
            title="Trust Scores"
            description="Per-claim confidence with evidence grounding"
            color={C.green}
            inStart={f(0.3)}
            outStart={f(3.5)}
          />
        </Sequence>
      )}
      {beat2Visible && (
        <Sequence from={f(4)} durationInFrames={f(4.5)}>
          <CapabilityBeat
            number="02"
            title="Provenance"
            description="Full lineage from source through every model"
            color={C.accent}
            inStart={f(0.3)}
            outStart={f(3.5)}
          />
        </Sequence>
      )}
      {beat3Visible && (
        <Sequence from={f(8)} durationInFrames={f(4.5)}>
          <CapabilityBeat
            number="03"
            title="Compliance"
            description="EU AI Act · HIPAA · SOX — audit-ready"
            color={C.amber}
            inStart={f(0.3)}
            outStart={f(3.5)}
          />
        </Sequence>
      )}
    </AbsoluteFill>
  );
};

/* ═══════════════════════════════════════════════════
   SCENE 5 — THE NUMBERS (32-42s)
   Big stats, centered, sequential
   ═══════════════════════════════════════════════════ */
const SceneNumbers: React.FC = () => {
  const frame = useCurrentFrame();

  const headerA = appear(frame, f(0.3), 16);

  const stats = [
    { value: "~15", unit: "tokens", desc: "Smaller than a tweet", start: f(1.0) },
    { value: "0.1", unit: "seconds", desc: "Real-time streaming", start: f(2.5) },
    { value: "20+", unit: "formats", desc: "Universal compatibility", start: f(4.0) },
  ];

  const sceneOut = fadeOut(frame, f(9.0));

  return (
    <AbsoluteFill
      style={{ background: C.bg, opacity: sceneOut }}
      className="flex flex-col items-center justify-center"
    >
      <div
        style={{
          opacity: headerA.opacity,
          transform: `translateY(${headerA.y}px)`,
          marginBottom: 80,
        }}
      >
        <Title size={24} weight={500} color={C.gray} tracking="0.15em">
          BY THE NUMBERS
        </Title>
      </div>

      <div className="flex items-start" style={{ gap: 120 }}>
        {stats.map((s) => {
          const a = appear(frame, s.start, 18);
          return (
            <div
              key={s.value}
              style={{
                opacity: a.opacity,
                transform: `translateY(${a.y}px)`,
                textAlign: "center",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  justifyContent: "center",
                  gap: 8,
                }}
              >
                <span
                  style={{
                    fontSize: 96,
                    fontWeight: 800,
                    color: C.white,
                    fontFamily: "'JetBrains Mono', monospace",
                    letterSpacing: "-0.04em",
                  }}
                >
                  {s.value}
                </span>
                <span
                  style={{
                    fontSize: 24,
                    fontWeight: 500,
                    color: C.gray,
                    fontFamily: "'SF Pro Display', 'Inter', sans-serif",
                  }}
                >
                  {s.unit}
                </span>
              </div>
              <div style={{ marginTop: 8 }}>
                <Title size={18} weight={400} color={C.gray} tracking="0em">
                  {s.desc}
                </Title>
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* ═══════════════════════════════════════════════════
   SCENE 6 — SIMPLICITY (42-50s)
   "One command. Every file."
   ═══════════════════════════════════════════════════ */
const SceneSimplicity: React.FC = () => {
  const frame = useCurrentFrame();

  const cmdA = appear(frame, f(0.5), 18);

  // Typing effect for the command
  const fullCmd = "pip install akf";
  const charsVisible = Math.min(
    fullCmd.length,
    Math.floor(
      interpolate(frame, [f(0.8), f(2.5)], [0, fullCmd.length], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    )
  );
  const typedCmd = fullCmd.slice(0, charsVisible);
  const showCursor = frame > f(0.8) && frame < f(3.5);
  const cursorBlink = Math.sin(frame * 0.3) > 0;

  const tagA = appear(frame, f(3.2), 18);
  const sceneOut = fadeOut(frame, f(7.2));

  return (
    <AbsoluteFill
      style={{ background: C.bg, opacity: sceneOut }}
      className="flex flex-col items-center justify-center"
    >
      {/* Terminal-style command */}
      <div
        style={{
          opacity: cmdA.opacity,
          transform: `translateY(${cmdA.y}px)`,
        }}
      >
        <div
          style={{
            padding: "28px 56px",
            borderRadius: 16,
            background: "#111111",
            border: "1px solid #222222",
          }}
        >
          <span
            style={{
              fontSize: 40,
              color: C.gray,
              fontFamily: "'JetBrains Mono', monospace",
              fontWeight: 500,
            }}
          >
            ${" "}
          </span>
          <span
            style={{
              fontSize: 40,
              color: C.white,
              fontFamily: "'JetBrains Mono', monospace",
              fontWeight: 600,
            }}
          >
            {typedCmd}
          </span>
          {showCursor && (
            <span
              style={{
                fontSize: 40,
                color: C.accent,
                fontFamily: "'JetBrains Mono', monospace",
                opacity: cursorBlink ? 1 : 0,
              }}
            >
              |
            </span>
          )}
        </div>
      </div>

      {/* Tagline below */}
      <div
        style={{
          opacity: tagA.opacity,
          transform: `translateY(${tagA.y}px)`,
          marginTop: 48,
        }}
        className="flex flex-col items-center gap-2"
      >
        <Title size={52} weight={600}>
          One command. Every file.
        </Title>
        <Title size={28} weight={400} color={C.gray} tracking="-0.01em">
          Full trust metadata — automatically.
        </Title>
      </div>
    </AbsoluteFill>
  );
};

/* ═══════════════════════════════════════════════════
   SCENE 7 — CTA (50-60s)
   "The file format for the AI era."
   ═══════════════════════════════════════════════════ */
const SceneCTA: React.FC = () => {
  const frame = useCurrentFrame();

  const headlineA = appear(frame, f(0.3), 24);
  const dividerWidth = interpolate(frame, [f(2.0), f(3.0)], [0, 160], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });
  const installsA = appear(frame, f(3.0), 18);
  const urlA = appear(frame, f(4.5), 18);

  // Final fade out
  const finalOut = fadeOut(frame, f(9.0), 20);

  return (
    <AbsoluteFill
      style={{ background: C.bg, opacity: finalOut }}
      className="flex flex-col items-center justify-center"
    >
      {/* Headline */}
      <div
        style={{
          opacity: headlineA.opacity,
          transform: `translateY(${headlineA.y}px)`,
        }}
      >
        <Title size={72} weight={700}>
          The file format
          <br />
          for the{" "}
          <span style={{ color: C.accent }}>AI era</span>.
        </Title>
      </div>

      {/* Divider */}
      <div
        style={{
          width: dividerWidth,
          height: 1,
          background: `linear-gradient(90deg, transparent, #333, transparent)`,
          marginTop: 48,
          marginBottom: 48,
        }}
      />

      {/* Install commands */}
      <div
        style={{
          opacity: installsA.opacity,
          transform: `translateY(${installsA.y}px)`,
        }}
        className="flex gap-10"
      >
        <div className="flex items-center gap-3">
          <Title size={16} weight={500} color={C.gray} tracking="0.05em">
            PYTHON
          </Title>
          <Title size={20} weight={500} color={C.white} tracking="0em">
            pip install akf
          </Title>
        </div>
        <div style={{ width: 1, height: 24, background: "#333" }} />
        <div className="flex items-center gap-3">
          <Title size={16} weight={500} color={C.gray} tracking="0.05em">
            NPM
          </Title>
          <Title size={20} weight={500} color={C.white} tracking="0em">
            npm install akf-format
          </Title>
        </div>
      </div>

      {/* URL + badge */}
      <div
        style={{
          opacity: urlA.opacity,
          transform: `translateY(${urlA.y}px)`,
          marginTop: 40,
        }}
        className="flex flex-col items-center gap-3"
      >
        <Title
          size={32}
          weight={600}
          color={C.accent}
          tracking="-0.01em"
          style={{ fontFamily: "'JetBrains Mono', monospace" }}
        >
          akf.dev
        </Title>
        <Title size={14} weight={500} color="#555" tracking="0.12em">
          OPEN FORMAT · MIT LICENSED
        </Title>
      </div>
    </AbsoluteFill>
  );
};

/* ═══════════════════════════════════════════════════
   SCENE 8 — LOGO HOLD (end)
   Clean .akf on black
   ═══════════════════════════════════════════════════ */
const SceneLogoHold: React.FC = () => {
  const frame = useCurrentFrame();

  const logoOpacity = interpolate(frame, [0, f(1.0)], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: EASE_OUT,
  });

  return (
    <AbsoluteFill
      style={{ background: C.bg }}
      className="flex items-center justify-center"
    >
      <span
        style={{
          opacity: logoOpacity,
          fontSize: 100,
          fontWeight: 800,
          color: C.accent,
          fontFamily: "'JetBrains Mono', 'SF Mono', monospace",
          letterSpacing: "-0.03em",
        }}
      >
        .akf
      </span>
    </AbsoluteFill>
  );
};

/* ═══════════════════════════════════════════════════
   MAIN COMPOSITION
   ═══════════════════════════════════════════════════ */
export const AKFDemo: React.FC = () => {
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      {/* Scene 1: Hook (0-5s) */}
      <Sequence from={f(0)} durationInFrames={f(5)}>
        <SceneHook />
      </Sequence>

      {/* Scene 2: Problem (5-12s) */}
      <Sequence from={f(5)} durationInFrames={f(7)}>
        <SceneProblem />
      </Sequence>

      {/* Scene 3: Reveal (12-20s) */}
      <Sequence from={f(12)} durationInFrames={f(8)}>
        <SceneReveal />
      </Sequence>

      {/* Scene 4: Capabilities (20-32s) */}
      <Sequence from={f(20)} durationInFrames={f(12)}>
        <SceneCapabilities />
      </Sequence>

      {/* Scene 5: Numbers (32-42s) */}
      <Sequence from={f(32)} durationInFrames={f(10)}>
        <SceneNumbers />
      </Sequence>

      {/* Scene 6: Simplicity (42-50s) */}
      <Sequence from={f(42)} durationInFrames={f(8)}>
        <SceneSimplicity />
      </Sequence>

      {/* Scene 7: CTA (50-60s) */}
      <Sequence from={f(50)} durationInFrames={f(10)}>
        <SceneCTA />
      </Sequence>
    </AbsoluteFill>
  );
};
